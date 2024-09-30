"""
CSC148, Winter 2023
Assignment 1

This code is provided solely for the personal and private use of
students taking the CSC148 course at the University of Toronto.
Copying for purposes other than this use is expressly prohibited.
All forms of distribution of this code, whether as given or with
any changes, are expressly prohibited.

All of the files in this directory and all subdirectories are:
Copyright (c) 2022 Bogdan Simion, Diane Horton, Jacqueline Smith
"""
import datetime
from math import ceil
from typing import Optional
from bill import Bill
from call import Call

# Constants for the month-to-month contract monthly fee and term deposit
MTM_MONTHLY_FEE = 50.00
TERM_MONTHLY_FEE = 20.00
TERM_DEPOSIT = 300.00

# Constants for the included minutes and SMSs in the term contracts (per month)
TERM_MINS = 100

# Cost per minute and per SMS in the month-to-month contract
MTM_MINS_COST = 0.05

# Cost per minute and per SMS in the term contract
TERM_MINS_COST = 0.1

# Cost per minute and per SMS in the prepaid contract
PREPAID_MINS_COST = 0.025


class Contract:
    """ A contract for a phone line

    This class is not to be changed or instantiated. It is an Abstract Class.

    === Public Attributes ===
    start:
         starting date for the contract
    bill:
         bill for this contract for the last month of call records loaded from
         the input dataset
    """
    start: datetime.date
    bill: Optional[Bill]

    def __init__(self, start: datetime.date) -> None:
        """ Create a new Contract with the <start> date, starts as inactive
        """
        self.start = start
        self.bill = None

    def new_month(self, month: int, year: int, bill: Bill) -> None:
        """ Advance to a new month in the contract, corresponding to <month> and
        <year>. This may be the first month of the contract.
        Store the <bill> argument in this contract and set the appropriate rate
        per minute and fixed cost.

        DO NOT CHANGE THIS METHOD
        """
        raise NotImplementedError

    def bill_call(self, call: Call) -> None:
        """ Add the <call> to the bill.

        Precondition:
        - a bill has already been created for the month+year when the <call>
        was made. In other words, you can safely assume that self.bill has been
        already advanced to the right month+year.
        """
        self.bill.add_billed_minutes(ceil(call.duration / 60.0))

    def cancel_contract(self) -> float:
        """ Return the amount owed in order to close the phone line associated
        with this contract.

        Precondition:
        - a bill has already been created for the month+year when this contract
        is being cancelled. In other words, you can safely assume that self.bill
        exists for the right month+year when the cancelation is requested.
        """
        self.start = None
        return self.bill.get_cost()


class TermContract(Contract):
    """ A type of contract for a phone line

        There is a starting deposit,
        which can only be taken back if the contract is seen
        through from start to end date.

        If canceled early, the deposit is not returned to the customer.

        If contract is canceled after the end date,
        then the deposit is returned minus the additional months pay

        This contract also receives free minutes per month,
        which refresh every month

    === Public Attributes ===
    end:
        end date for the term contract
    """
    end: datetime.date
    month: int
    year: int

    def __init__(self, start: datetime.date, end: datetime.date) -> None:
        Contract.__init__(self, start)
        self.end = end
        self.bill = Bill()
        self.month = start.month
        self.year = start.year

    def new_month(self, month: int, year: int, bill: Bill) -> None:
        self.bill = bill
        self.bill.set_rates("TERM", TERM_MINS_COST)
        self.month = month
        self.year = year

        if self.month == self.start.month and self.year == self.start.year:
            self.bill.add_fixed_cost(TERM_MONTHLY_FEE + TERM_DEPOSIT)
        else:
            self.bill.add_fixed_cost(TERM_MONTHLY_FEE)

        self.bill.free_min = 0
        self.bill.billed_min = 0

    def bill_call(self, call: Call) -> None:
        remaining_free_min = TERM_MINS - self.bill.free_min
        call_time = ceil(call.duration / 60)

        if remaining_free_min - call_time >= 0:
            self.bill.add_free_minutes(call_time)
        elif remaining_free_min - call_time < 0:
            if remaining_free_min > 0:
                self.bill.add_free_minutes(remaining_free_min)
                self.bill.add_billed_minutes(call_time - remaining_free_min)
            elif remaining_free_min <= 0:
                self.bill.add_billed_minutes(call_time)

    def cancel_contract(self) -> float:
        if (self.month >= self.end.month) and (self.year >= self.end.year):
            self.start = None
            self.end = None
            return self.bill.get_cost() - TERM_DEPOSIT
        else:
            self.start = None
            self.end = None
            return self.bill.get_cost()


class MTMContract(Contract):
    """ A type of contract for a phone line

        no deposit, higher rates for calls, no free minutes.
        can be canceled at any time without downside

    === Public Attributes ===
    start:
         starting date for the term contract
    """

    def __init__(self, start: datetime.date) -> None:
        Contract.__init__(self, start)
        self.bill = Bill()
        self.bill.set_rates("MTM", MTM_MINS_COST)

    def new_month(self, month: int, year: int, bill: Bill) -> None:
        self.bill = bill
        self.bill.add_fixed_cost(MTM_MONTHLY_FEE)
        self.bill.billed_min = 0
        self.bill.set_rates("MTM", MTM_MINS_COST)


class PrepaidContract(Contract):
    """ A type of contract for a phone line

            customer prepays any amount

            when balance is negative-
            this is the amount of credit the customer has

        === Public Attributes ===
        start:
             starting date for the term contract
        balance:
                the amount of credit the
                customer has (AKA how much they pre paid)
    """
    balance: float

    def __init__(self, start: datetime.date, balance: float) -> None:
        Contract.__init__(self, start)
        self.bill = Bill()
        self.balance = 0 - balance
        self.bill.add_fixed_cost(self.balance)

    def new_month(self, month: int, year: int, bill: Bill) -> None:
        self.balance = self.bill.get_cost()

        if self.balance > -10:
            self.balance -= 25

        self.bill = bill
        self.bill.billed_min = 0
        self.bill.set_rates("PREPAID", PREPAID_MINS_COST)

        self.bill.add_fixed_cost(self.balance)

    def cancel_contract(self) -> float:
        self.start = None
        self.balance = self.bill.get_cost()
        if self.balance <= 0:
            return 0
        else:
            return self.balance


if __name__ == '__main__':
    import python_ta

    python_ta.check_all(config={
        'allowed-import-modules': [
            'python_ta', 'typing', 'datetime', 'bill', 'call', 'math'
        ],
        'disable': ['R0902', 'R0913'],
        'generated-members': 'pygame.*'
    })
