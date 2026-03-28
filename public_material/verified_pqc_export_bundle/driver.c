#include <stdint.h>
#include <stdio.h>
#include "kernel.h"

int main(void) {
  for (uint64_t i = 0; i <= 4; ++i) {
    printf("%llu:%llu\n",
      (unsigned long long)i,
      (unsigned long long)verified_pqc_accept_all_checks(i));
  }
  return 0;
}