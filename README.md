# QuickRecord
Please see the instructions below:

Video Demo: https://www.youtube.com/watch?v=LcTDTIHJFMQ

## Description

The application is for those who want to record their financial status as an accountant. Then, they are able to share the account information with their friends or family members, so they can collaborate with each other.

## Assumption:

Users will need to have a basic understanding of accounting and bookkeeping.

## Features
- View Balance Statement and Income Statement

  After registering, users can see the overview financial statement such as Balance Statement and Income Statement. They will be shown by the type - Asset, Liability, Revenue or Expense, and account names that users created.

- Create Customized Accounts

  There are no default accounts. Users must create an account name and its type as their first use.
  - Type should be only Asset, liability, revenue, or expense.
  - Account name should be logical by the creater.

- Record Transactions

  After creating account names, they can record, for example,
  - debit: Cash
  - credit: Revenue - Salary from XXX Inc.
  - amount: $100,000


  - debit: XXX Expense
  - credit: Cash
  - amount: $1,000
  
  ***'/' will show the balance is $99,000, and the income is $99,000.***

- Send A Friend Request
  - Send Request: users can send friend requests to other validated users.
  - Accept: By clicking accepting, they can share an account.
  - Reject: It also delete the friend request from the other side, but it can be asked again.
  - Delete:
    - Once one of them deletes the friend name, the delete process will remove both of friend statuses.
    - Cannot share the change of account message again, but the historical records do not remove.

- Share An Account With Your Friends

  When users create an account name, they can choose whether share the account information with friends. If they want to, every change of that account will be shown on the page named "Shared Account Message"

  ***Notice: It will not show the entire journal entry if the user's friend only can see the messages either a debit account or credit account. Only show the account users chose to share with friends.***

- View Shared Account Messages (if you have shared with one of your friends)

  Browse all the changes of shared accounts.

- View History of Transactions

  Browse all transactions excluding shared accounts users have not recorded by themself.

- Check out The Balance of the Account On When You Select

  Browse the balance on a specific date. This function help to focuse on one account at a time.
  If you want to check the balance at a specific time,
  You can input the account name and choose the time point you want to check. 
  For instance, today is 2021/12/15 and cash balance is $100. If select the date before 2021/12/15, the balance would change. 
  If select the date at 2021/12/15 or after, cash balance is $100.

- View The Graph of All Accounts

  Visualize all accounts' balances
  We choose the bar chart to display the account balance because it is easy to understand.
  This idea of function is drive from providing useful insight by visual data. 
  In this function, you can review all of your account balances and check which is the highest one and which is the lowest one at the glance.

## Language used
- python flask (Most)
- javascript
- SQL
- CSS
- HTML

## Getting start
```
git clone
```
```
pip install -r requirements.txt
```

If using VS Code, setting up environment first
```
$env:FLASK_APP = "application"
```
```
flask run
```

### Coworker Github: remykung
