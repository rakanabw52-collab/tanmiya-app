create or replace function public.hd_invoice_number_key(value text)
returns text language sql immutable parallel safe set search_path = ''
as $function$
 select lower(regexp_replace(translate(normalize(coalesce(value,''),NFKC),'٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹','01234567890123456789'),'[[:space:]]+','','g'))
$function$;
create or replace function public.hd_invoice_numbers_unique(payload jsonb)
returns boolean language sql immutable parallel safe set search_path = ''
as $function$
 select case when jsonb_typeof(payload) is distinct from 'array' then false else
 not exists (
  select public.hd_invoice_number_key(item->>'number')
  from jsonb_array_elements(case when jsonb_typeof(payload)='array' then payload else '[]'::jsonb end) as item
  where public.hd_invoice_number_key(item->>'number')<>''
  group by public.hd_invoice_number_key(item->>'number')
  having count(*)>1
 ) end
$function$;
alter table public.invoices
 add constraint hd_invoice_numbers_unique_check
 check (id<>'_all' or public.hd_invoice_numbers_unique(data)) not valid;

-- Run after archived duplicate cleanup is complete.
alter table public.invoices validate constraint hd_invoice_numbers_unique_check;
