# CDS Analytical View Syntax Guide

Copy-paste syntax templates for general-purpose/analytical CDS views (no RAP composition). For root/child/projection view entities and association syntax, see [Skill: cds-view-entities]'s reference instead.

## Basic View Entity

```cds
@AccessControl.authorizationCheck: #CHECK
@EndUserText.label: 'Sales Order'
define view entity ZI_SalesOrder
  as select from zsalesorder
{
  key order_id       as OrderId,
      customer_id    as CustomerId,
      order_date     as OrderDate,
      net_amount     as NetAmount,
      currency_code  as CurrencyCode,
      status         as Status,
      created_by     as CreatedBy,
      created_at     as CreatedAt,
      last_changed_at as LastChangedAt
}
```

## Expressions & Built-in Functions

```cds
// Cast
cast( amount as abap.dec(15,2) ) as ConvertedAmount,

// Simple CASE
case status
  when 'N' then 'New'
  when 'A' then 'Approved'
  else 'Unknown'
end as StatusText,

// Searched CASE
case when net_amount > 10000 then 'High'
     when net_amount > 1000  then 'Medium'
     else 'Low'
end as PriorityCategory,

// Arithmetic
quantity * unit_price as TotalPrice,

// Strings
concat( first_name, concat( ' ', last_name ) ) as FullName,
substring( postal_code, 1, 2 )                 as Region,
length( description )                          as DescLength,
upper( country_code )                          as CountryUpper,

// Date & time
dats_days_between( start_date, end_date ) as DurationDays,
dats_add_days( order_date, 30 )           as DueDate,
tstmp_current_utctimestamp()              as CurrentTimestamp,

// Session variables
$session.user            as CurrentUser,
$session.system_date     as SystemDate,
$session.system_language as SystemLanguage,
```

## Aggregate Expressions

```cds
define view entity ZI_OrderSummary
  as select from zsalesorder
{
  key customer_id as CustomerId,
      count(*)                      as OrderCount,
      sum( net_amount )             as TotalAmount,
      avg( net_amount as abap.dec(15,2) ) as AvgAmount,
      min( order_date )             as FirstOrderDate,
      max( order_date )             as LastOrderDate
}
group by customer_id
```

Every non-aggregated field in the `SELECT` list must appear in `group by`, or activation fails.

## Input Parameters

```cds
define view entity ZI_SalesOrderByDate
  with parameters
    p_date : abap.dats
  as select from zsalesorder
{
  key order_id   as OrderId,
      order_date as OrderDate,
      net_amount as NetAmount
}
where order_date >= $parameters.p_date
```

```abap
SELECT FROM zi_salesorderbydate( p_date = @lv_date )
  FIELDS OrderId, OrderDate, NetAmount
  INTO TABLE @DATA(lt_orders).
```

## Joins

```cds
define view entity ZI_OrderWithCustomer
  as select from zsalesorder as so
  inner join zcustomer as cust
    on so.customer_id = cust.customer_id
{
  key so.order_id      as OrderId,
      cust.customer_name as CustomerName,
      so.net_amount     as NetAmount
}
```

| Join Type   | Keyword            | Behavior                       |
| ----------- | ------------------ | ------------------------------- |
| Inner       | `inner join`       | Only matching rows             |
| Left Outer  | `left outer join`  | All from left + matching right |
| Right Outer | `right outer join` | All from right + matching left |
| Cross       | `cross join`       | Cartesian product               |

Prefer associations over joins when possible — see [Skill: cds-view-entities]'s reference for association syntax; associations are lazily resolved and support path expressions, a join always executes.

## UI Annotations & Metadata Extensions

```cds
@UI.headerInfo: {
  typeName: 'Sales Order',
  typeNamePlural: 'Sales Orders',
  title: { type: #STANDARD, value: 'OrderId' }
}
```

Metadata extension (recommended home for UI annotations — requires `@Metadata.allowExtensions: true` on the view):

```cds
@Metadata.layer: #CUSTOMER
annotate view ZC_SalesOrder with
{
  @UI.facet: [{
    id: 'GeneralInfo',
    type: #IDENTIFICATION_REFERENCE,
    label: 'General Information',
    position: 10
  }]

  @UI.lineItem: [{ position: 10, importance: #HIGH }]
  @UI.identification: [{ position: 10 }]
  OrderId;

  @UI.lineItem: [{ position: 20 }]
  @UI.identification: [{ position: 20 }]
  @UI.selectionField: [{ position: 10 }]
  CustomerId;
}
```
