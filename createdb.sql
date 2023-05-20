create table expense(
    id integer primary key,
    amount integer,
    created datetime,
    category varchar(255),
    FOREIGN KEY(category) REFERENCES category(name)
);

create table category(
    name varchar(255) primary key
);
