-- SQLite
-- reset account table
drop table account;
create table account (
    id integer primary KEY,
    user_id integer,
    type text not null,
    name text not null,
    note text,
    initial numeric default 0,
    amount numeric default 0,
    FOREIGN KEY(user_id) REFERENCES users(id)
);