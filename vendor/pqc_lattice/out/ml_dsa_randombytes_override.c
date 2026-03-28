#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <openssl/evp.h>

static unsigned char Key[32];
static unsigned char V[16];
static int trace_on = -1; // -1 unknown, 0 off, 1 on
static FILE *trace_fp = NULL;

static void trace_init(){
  if(trace_on != -1) return;
  const char *t = getenv("RNG_TRACE");
  trace_on = (t && t[0] && t[0] != '0') ? 1 : 0;
  if(trace_on){
    const char *p = getenv("RNG_TRACE_FILE");
    if(p && p[0]){ trace_fp = fopen(p, "ab"); }
    if(!trace_fp) trace_on = 0;
  }
}

static void trace_hex(const char *prefix, const unsigned char *buf, size_t n){
  if(!trace_on) return;
  static const char *h = "0123456789abcdef";
  fprintf(trace_fp, "%s", prefix);
  for(size_t i=0;i<n;i++){ fputc(h[buf[i]>>4], trace_fp); fputc(h[buf[i]&0xF], trace_fp); }
  fputc('\n', trace_fp);
  fflush(trace_fp);
}

static void handle_err(void){ abort(); }

static void AES256_ECB(const unsigned char *key, const unsigned char *ctr, unsigned char *out){
  EVP_CIPHER_CTX *ctx = EVP_CIPHER_CTX_new();
  if(!ctx) handle_err();
  if(1!=EVP_EncryptInit_ex(ctx, EVP_aes_256_ecb(), NULL, key, NULL)) handle_err();
  if(1!=EVP_CIPHER_CTX_set_padding(ctx, 0)) handle_err();
  int outl=0;
  if(1!=EVP_EncryptUpdate(ctx, out, &outl, ctr, 16)) handle_err();
  EVP_CIPHER_CTX_free(ctx);
}

static void inc_V(unsigned char *v){
  for(int j=15;j>=0;j--){
    if(v[j]==0xff) v[j]=0x00; else { v[j]++; break; }
  }
}

static void AES256_CTR_DRBG_Update(const unsigned char *provided_data, unsigned char *Key_, unsigned char *V_){
  unsigned char temp[48];
  for(int i=0;i<3;i++){
    inc_V(V_);
    AES256_ECB(Key_, V_, temp+16*i);
  }
  if(provided_data){ for(int i=0;i<48;i++) temp[i]^=provided_data[i]; }
  memcpy(Key_, temp, 32);
  memcpy(V_, temp+32, 16);
}

void randombytes_init(unsigned char *entropy_input, unsigned char *personalization_string, int security_strength){
  (void)security_strength;
  trace_init();
  unsigned char seed_material[48];
  memcpy(seed_material, entropy_input, 48);
  if(personalization_string){ for(int i=0;i<48;i++) seed_material[i]^=personalization_string[i]; }
  memset(Key,0,32); memset(V,0,16);
  AES256_CTR_DRBG_Update(seed_material, Key, V);
  trace_hex("init:", seed_material, 48);
}

static void drbg_generate(unsigned char *x, size_t xlen){
  trace_init();
  while(xlen>0){
    inc_V(V);
    unsigned char block[16];
    AES256_ECB(Key, V, block);
    size_t n = xlen > 15 ? 16 : xlen;
    memcpy(x, block, n);
    x+=n; xlen-=n;
  }
  AES256_CTR_DRBG_Update(NULL, Key, V);
}

int randombytes(unsigned char *x, unsigned long long xlen){
  unsigned char *base = x; size_t n = (size_t)xlen;
  drbg_generate(x, n);
  if(trace_on && n){
    fprintf(trace_fp, "len:%zu\n", n);
    size_t lim = n > 256 ? 256 : n; trace_hex("gen:", base, lim);
  }
  return 0;
}

/* PQClean expects PQCLEAN_randombytes (via randombytes.h). */
int PQCLEAN_randombytes(uint8_t *x, size_t xlen){
  unsigned char *base = x; size_t n = xlen;
  drbg_generate(x, n);
  if(trace_on && n){
    fprintf(trace_fp, "len:%zu\n", n);
    size_t lim = n > 256 ? 256 : n; trace_hex("gen:", base, lim);
  }
  return 0;
}
