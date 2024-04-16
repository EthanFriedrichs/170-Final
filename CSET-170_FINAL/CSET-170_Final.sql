create database bank;
use bank;

drop table accounts;
create table accounts (username varchar(255) primary key, first_name varchar(255), last_name varchar(255), social varchar(255), address varchar(255), phone_number varchar(255), pass varchar(255), is_admin varchar(5) default "false", approved varchar(5) default "false");
select * from accounts;
insert into accounts values ("Admin1", "admin", "1", "000-00-0000", "None", "None", "aaa", "true", "true");
update accounts set is_admin = "true", approved = "true" where username = "Admin1";

drop table bank_number;
create table bank_number (acct_numb int primary key auto_increment, username varchar(255), balance float default 0,
foreign key (username) references accounts(username));
select * from bank_number;
insert into bank_number (username) values ("Admin1");
insert into bank_number (username) values ("test_2");
update bank_number set balance = 30.0 where username = "david";