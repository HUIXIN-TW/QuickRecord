-- SQLite
-- reset account table
drop table xxxxxxxxxxxx;
create table accounts (
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
    asker_id integer,
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


drop table transactions;
create table transactions (
    id integer primary KEY,
    user_id integer not null,
    debit text not null,
    credit text not null,
    amount numeric default 0,
    transacted TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    debitshare text,
    debitsharestatus text default "None",
    debitshareaccountid integer,
    creditshare text,
    creditsharestatus text default "None",
    creditshareaccountid integer,
    note text,
    FOREIGN KEY(user_id) REFERENCES users(id)
);

drop table messages;
create table messages (
    id integer primary KEY,
    transaction_id integer, 
    creater_id integer,
    creater_name text,
    receiver_id integer, 
    receiver_name text,
    account_id integer, 
    accountname text, 
    amount numeric default 0, 
    transacted timestamp, 
    sharestatus text, 
    note text,
    FOREIGN KEY(transaction_id) REFERENCES transactions(id)
);

Delete from accounts;
Delete from friends;
Delete from messages;
Delete from transactions;
Delete from users;