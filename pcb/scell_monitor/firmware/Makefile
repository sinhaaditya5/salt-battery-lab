# Host build of the SCM-1 supervision core + unit tests (no target toolchain needed).
CC ?= cc
CFLAGS = -std=c11 -Wall -Wextra -Werror -O1 -I.
test: limits.h test/test_core.c scm_core.c scm_core.h
	$(CC) $(CFLAGS) -o test/test_core test/test_core.c scm_core.c
	./test/test_core
	$(CC) $(CFLAGS) -o test/test_drv test/test_drv.c drv_max31856.c test/hal_stub.c
	./test/test_drv
	$(CC) $(CFLAGS) -DSCM_HOST_SYNTAX_CHECK -fsyntax-only main_stm32.c
limits.h: gen_limits.py ../../../params/scell_params.py
	python3 gen_limits.py
clean:
	rm -f test/test_core test/test_drv
.PHONY: test clean
