-- SQLite
-- reset account table
drop table account;
create table account (
    id integer primary KEY,
    user_id integer,
    type text,
    name text,
    note text,
    amount numeric default 0
);