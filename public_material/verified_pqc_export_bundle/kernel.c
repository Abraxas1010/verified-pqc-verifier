/* verified_pqc_accept_all_checks: Nat -> Nat */
#include <stdint.h>
uint64_t verified_pqc_accept_all_checks(uint64_t passed_checks) {
  return passed_checks == 4 ? 1 : 0;
}
