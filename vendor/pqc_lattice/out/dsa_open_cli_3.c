#include <stdio.h>
#include <string.h>
#include <stdint.h>
#include <stdlib.h>
#include <ctype.h>
#include "api.h"

#define crypto_sign_open PQCLEAN_MLDSA65_CLEAN_crypto_sign_open
#define CRYPTO_PUBLICKEYBYTES PQCLEAN_MLDSA65_CLEAN_CRYPTO_PUBLICKEYBYTES

static int hexval(int c){ if('0'<=c&&c<='9')return c-'0'; if('a'<=c&&c<='f')return c-'a'+10; if('A'<=c&&c<='F')return c-'A'+10; return -1; }
static size_t hex2bin(const char *hex, uint8_t *out, size_t maxout){ size_t n=0; while(hex[0]&&hex[1]){ int hi=hexval(hex[0]); int lo=hexval(hex[1]); if(hi<0||lo<0||n>=maxout) break; out[n++]=(uint8_t)((hi<<4)|lo); hex+=2; } return n; }

int main(void){
  char *pk_hex=NULL,*sm_hex=NULL,*m_hex=NULL; size_t mlen=0,smlen=0; char line[1<<16];
  while(fgets(line,sizeof(line),stdin)){
    char *p=line; while(*p&&isspace((unsigned char)*p)) p++;
    if(strncmp(p,"pk",2)==0){
      char *eq=strchr(p,'='); if(!eq)continue; eq++;
      while(*eq&&isspace((unsigned char)*eq))eq++;
      size_t L=strlen(eq);
      while(L&&(eq[L-1]=='\n'||eq[L-1]=='\r'||isspace((unsigned char)eq[L-1]))) eq[--L]=0;
      pk_hex=(char*)malloc(L+1); if(!pk_hex){fprintf(stderr,"oom\n"); return 9;}
      memcpy(pk_hex,eq,L+1);
    }
    else if(strncmp(p,"mlen",4)==0){ if(sscanf(p, "mlen = %zu", &mlen)!=1) mlen=0; }
    else if(strncmp(p,"smlen",5)==0){ if(sscanf(p, "smlen = %zu", &smlen)!=1) smlen=0; }
    else if(strncmp(p,"sm",2)==0){
      char *eq=strchr(p,'='); if(!eq)continue; eq++;
      while(*eq&&isspace((unsigned char)*eq))eq++;
      size_t L=strlen(eq);
      while(L&&(eq[L-1]=='\n'||eq[L-1]=='\r'||isspace((unsigned char)eq[L-1]))) eq[--L]=0;
      sm_hex=(char*)malloc(L+1); if(!sm_hex){fprintf(stderr,"oom\n"); return 9;}
      memcpy(sm_hex,eq,L+1);
    }
    else if(strncmp(p,"msg",3)==0){
      char *eq=strchr(p,'='); if(!eq)continue; eq++;
      while(*eq&&isspace((unsigned char)*eq))eq++;
      size_t L=strlen(eq);
      while(L&&(eq[L-1]=='\n'||eq[L-1]=='\r'||isspace((unsigned char)eq[L-1]))) eq[--L]=0;
      m_hex=(char*)malloc(L+1); if(!m_hex){fprintf(stderr,"oom\n"); return 9;}
      memcpy(m_hex,eq,L+1);
    }
  }
  if(!pk_hex||!sm_hex||!m_hex){ fprintf(stderr,"missing pk/sm/msg\n"); return 2; }
  uint8_t pk[CRYPTO_PUBLICKEYBYTES];
  size_t pkb=hex2bin(pk_hex,pk,sizeof(pk)); free(pk_hex);
  uint8_t *sm=malloc(smlen); uint8_t *mexp=malloc(mlen); uint8_t *mout=malloc(smlen);
  if(!sm||!mexp||!mout){ fprintf(stderr,"oom\n"); return 9; }
  size_t smn=hex2bin(sm_hex,sm,smlen); free(sm_hex);
  size_t mn=hex2bin(m_hex,mexp,mlen); free(m_hex);
  if(pkb!=CRYPTO_PUBLICKEYBYTES||smn!=smlen||mn!=mlen){ fprintf(stderr,"size mismatch\n"); return 3; }
  size_t moutlen=0; int rc=crypto_sign_open(mout,&moutlen,sm,smlen,pk);
  if(rc!=0){ fprintf(stderr,"open failed\n"); return 4; }
  if(moutlen!=mlen||memcmp(mout,mexp,mlen)!=0){ fprintf(stderr,"msg mismatch\n"); return 5; }
  printf("ok\n"); return 0;
}
