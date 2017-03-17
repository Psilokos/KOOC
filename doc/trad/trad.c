#include <stdlib.h>
#include <string.h>
#include "trad.h"


//Class: Base
//member functions
void    __kfct_Base_fct_v_pU_Base_E_ppi1s(Base *self, char **a) {
    //do things
}

int     __kfct_Base_fct2_i4s_pU_Base_E_i4s_i4s(Base *self, int a, int b) {
    return (a * b);
}


//destruction
void    __kfct_Base_clean_v_pU_Base_E(Base *self) {
    free(self->__kvar_Base_truc_pi1s);
}

void    __kfct_Base_delete_v_pU_Base_E(Base *self) {
    self->vt->clean(self);
    free(self->vt);
    free(self);
}


//construction
Base    *__kfct_Base_alloc_pU_Base_E_v(void) {
    return (malloc(sizeof(Base)));
}

void    __kfct_Base_init_v_pU_Base_E_pi1s_i4s(Base *self, char *a, int b) {
    struct __itf_Base *vt = malloc(sizeof(struct __itf_Base));

    if (!vt)
        return;

    vt->clean = &__kfct_Base_clean_v_pU_Base_E;
    vt->dtor = &__kfct_Base_delete_v_pU_Base_E;
    vt->fct2_i4s_i4s_i4s = &__kfct_Base_fct2_i4s_pU_Base_E_i4s_i4s;
    self->vt = vt;

    self->__kvar_Base_truc_pi1s = a;
    self->__kvar_Base_pouet_i4s = b;
}

Base    *__kfct_Base_new_pU_Base_E_pi1s_i4s(char *a, int b) {
    Base *new = __kfct_Base_alloc_pU_Base_E_v();

    if (!new)
        return (NULL);
    __kfct_Base_init_v_pU_Base_E_pi1s_i4s(new, a, b);

    return (new);
}



//Class: Heir
//member functions
double  __kfct_Heir_fct_i8s_pU_Heir_E_i4s_f8s(Heir *self, int a, double b) {
    return (a * b);
}

int     __kfct_Heir_fct2_i4s_pU_Heir_E_i4s_i4s(Heir *self, int a, int b) {
    return (a + b);
}


//destructor
void    __kfct_Heir_clean_v_pU_Heir_E(Heir *self) {
    __kfct_Base_clean_v_pU_Base_E(&self->parent);
}

void    __kfct_Heir_delete_v_pU_Heir_E(Heir *self) {
    __kfct_Heir_clean_v_pU_Heir_E(self);

    free(self->parent.vt);
    free(self);
}


//constructor
Heir    *__kfct_Heir_alloc_pU_Heir_E_v(void) {
    return (malloc(sizeof(Heir)));
}

void    __kfct_Heir_init_v_pU_Heir_E_pi1s_i4s_f8s(Heir *self, char *a, int b, double c) {
    __kfct_Base_init_v_pU_Base_E_pi1s_i4s(&self->parent, a, b);
    self->__kvar_Heir_rePouet_i4s = 0;
    self->__kvar_Heir_lolilol_f8s = c;
}

Heir    *__kfct_Heir_new_pU_Heir_E_pi1s_i4s_f8s(char *a, int b, double c) {
    Heir *new = __kfct_Heir_alloc_pU_Heir_E_v();

    __kfct_Heir_init_v_pU_Heir_E_pi1s_i4s_f8s(new, a, b, c);

    return (new);
}



//Pouet
//member functions
int     __kfct_Pouet_zerg_i4s_v() {
    return (123456);
}


//destructor
void    __kfct_Pouet_clean_v_pU_Pouet_E(__attribute__ (( unused )) Pouet *self) {}

void    __kfct_Pouet_delete_v_pU_Pouet_E(Pouet *self) {
    __kfct_Pouet_clean_v_pU_Pouet_E(self);
    free(self);
}

//constructor
Pouet   *__kfct_Pouet_alloc_pU_Pouet_E_v(void) {
    return (malloc(sizeof(Pouet)));
}

void    __kfct_Pouet_init_v_pU_Pouet_E(__attribute__ (( unused )) Pouet *self) {}

Pouet   *__kfct_Pouet_new_pU_Pouet_E_v(void) {
    Pouet *new = __kfct_Pouet_alloc_pU_Pouet_E_v();

    __kfct_Pouet_init_v_pU_Pouet_E(new);
    return (new);
}
