-- SQLite
-- reset account table
drop table account;
create table account (
    id integer primary KEY,
    user_id integer not null,
    type text not null,
    name text not null,
    share text,
    sharestatus text,
    shareaccountid integer,
    note text,
    initial numeric default 0,
    amount numeric default 0,
    FOREIGN KEY(user_id) REFERENCES users(id)
);

drop table friends;
create table friends (
    id integer primary KEY,
    user_id integer,
    username text not null,
    status text not null,
    FOREIGN KEY(user_id) REFERENCES users(id)
);

Delete from transactions;

drop table transactions;
create table transactions (
    id integer primary KEY,
    user_id integer not null,
    debit text not null,
    credit text not null,
    amount numeric default 0,
    transacted TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    share text default "",
    sharestatus text default "None",
    note text,
    FOREIGN KEY(user_id) REFERENCES users(id)
);