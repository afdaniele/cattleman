create table if not exists clusters
(
    id TEXT not null
        constraint clusters_pk
        primary key,
    date TEXT not null,
    enabled INTEGER not null,
    value BLOB not null
);

create unique index if not exists clusters_id_uindex
    on clusters (id);


create table if not exists nodes
(
    id TEXT not null
        constraint nodes_pk
            primary key,
    date TEXT not null,
    enabled INTEGER not null,
    value BLOB not null
);

create unique index if not exists nodes_id_uindex
    on nodes (id);


create table if not exists applications
(
    id TEXT not null
        constraint applications_pk
            primary key,
    date TEXT not null,
    enabled INTEGER not null,
    value BLOB not null
);

create unique index if not exists applications_id_uindex
    on applications (id);


create table if not exists services
(
    id TEXT not null
        constraint services_pk
            primary key,
    date TEXT not null,
    enabled INTEGER not null,
    value BLOB not null
);

create unique index if not exists services_id_uindex
    on services (id);


create table if not exists pods
(
    id TEXT not null
        constraint pods_pk
            primary key,
    date TEXT not null,
    enabled INTEGER not null,
    value BLOB not null
);

create unique index if not exists pods_id_uindex
    on pods (id);


create table if not exists dns_records
(
    id TEXT not null
        constraint dns_records_pk
            primary key,
    date TEXT not null,
    enabled INTEGER not null,
    value BLOB not null
);

create unique index if not exists dns_records_id_uindex
    on dns_records (id);


create table if not exists ip_addresses
(
    id TEXT not null
        constraint ip_addresses_pk
            primary key,
    date TEXT not null,
    enabled INTEGER not null,
    value BLOB not null
);

create unique index if not exists ip_addresses_id_uindex
    on ip_addresses (id);


create table if not exists ports
(
    id TEXT not null
        constraint ports_pk
            primary key,
    date TEXT not null,
    enabled INTEGER not null,
    value BLOB not null
);

create unique index if not exists ports_id_uindex
    on ports (id);


create table if not exists requests
(
    id TEXT not null
        constraint requests_pk
            primary key,
    date TEXT not null,
    enabled INTEGER not null,
    value BLOB not null
);

create unique index if not exists requests_id_uindex
    on requests (id);