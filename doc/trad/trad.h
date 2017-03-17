// C

//Base
extern unsigned int  __kvar_Base_pignon_f4u;

typedef struct __kclass_Base Base;

struct __itf_Base {
    void (*clean)(struct __kclass_Base *self);
    void (*dtor)(struct __kclass_Base *self);
    int  (*fct2_i4s_i4s_i4s)(struct __kclass_Base *self, int a, int b);
};

struct      __kclass_Base {
    struct  __itf_Base *vt;
    char    *__kvar_Base_truc_pi1s;
    int     __kvar_Base_pouet_i4s;
};

//construction
Base    *__kfct_Base_alloc_pU_Base_E_v(void);                                       //alloc struct pointer
void    __kfct_Base_init_v_pU_Base_E_pi1s_i4s(Base *self, char *, int);             //init_vals
Base    *__kfct_Base_new_pU_Base_E_pi1s_i4s(char *, int);                           //ctor | calls alloc and init
//destruction
void    __kfct_Base_clean_v_pU_Base_E(Base *self);                                  //resets class variables
void    __kfct_Base_delete_v_pU_Base_E(Base *self);                                 //frees the class instance | calls clean
//user defined member methods
void    __kfct_Base_fct_v_pU_Base_E_ppi1s(Base *self, char **);
int     __kfct_Base_fct2_i4s_pU_Base_E_i4s_i4s(Base *self, int, int);



//Heir
typedef struct __kclass_Heir Heir;
struct      __kclass_Heir {
    Base    parent;
    double  __kvar_Heir_lolilol_f8s;
    int     __kvar_Heir_rePouet_i4s;
} __attribute__(( packed ));

//construction
Heir    *__kfct_Heir_alloc_pU_Heir_E_v(void);                                       //alloc
void    __kfct_Heir_init_v_pU_Heir_E_pi1s_i4s_f8s(Heir *self, char *, int, double); //init vals
Heir    *__kfct_Heir_new_pU_Heir_E_pi1s_i4s_f8s(char *, int, double);	            //ctor | calls alloc an init
//destruction
void    __kfct_Heir_clean_v_pU_Heir_E(Heir *self);                                  //resets class variables
void    __kfct_Heir_delete_v_pU_Heir_E(Heir *self);                                 //frees the class instance | calls clean
//user defined member methods
double  __kfct_Heir_fct_f8s_pU_Heir_E_i4s_f8s(Heir *self, int, double);
int     __kfct_Heir_fct2_i4s_pU_Heir_E_i4s_i4s(Heir *self, int, int);



//Pouet
typedef struct __kclass_Pouet Pouet;
struct __kclass_Pouet {
    float   __kvar_Pouet_rush_f4s;
};

//construction
Pouet   *__kfct_Pouet_alloc_pU_Pouet_E_v(void);                                     //alloc
void    __kfct_Pouet_init_v_pU_Pouet_E(Pouet *self);                                //init vals
Pouet   *__kfct_Pouet_new_pU_Pouet_E_v(void);                                       //ctor | calls alloc and init
//destruction
void    __kfct_Pouet_clean_v_pU_Pouet_E(Pouet *self);                               //resets class variables;
void    __kfct_Pouet_delete_v_pU_Pouet_E(Pouet *self);                              //fress the class instance | calls clean
//user defined non member methods
int     __kfct_Pouet_zerg_i4s_v(void);
