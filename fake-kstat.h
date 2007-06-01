struct tag_kstat_t
{
  struct tag_kstat_t *ks_next;
  char* ks_data;
  PRUint32 ks_data_size;
  int ks_ndata;
};

struct tag_kstat_ctl_t
{
  struct tag_kstat_t *kc_chain;
};

typedef struct tag_kstat_t kstat_t;
typedef struct tag_kstat_ctl_t kstat_ctl_t;

#define kstat_open() NULL
#define kstat_read(a,b,c) -1
#define kstat_close(x) -1

