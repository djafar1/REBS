# EDA

## Event: Insert Fine Notification

Data attributes:
- lastSent: NaN, P, N, C
- notificationType: P, C
Insights:
- They are not always the same
- Need to test if they are correlated

## Event: Payment

Data attributes:
- paymentAmount
- totalPaymentAmount
Insights:
- paymentAmount <= totalPaymentAmount
- the values are correlated

## Event: Appeal to Judge

Data attributes:
- dismissal: 'G', '#', 'C', 'T', 'E', 'NIL', 'F', 'M', 'U', 'D', 'K', 'N', 'Q', '@', 'V', '3', 'I', 'A', '5', 'B'
- matricola (can be completely ignored only one value = 0.0)

## Event: Add Penalty

Data attributes:
- amount
Insights:
- Not always correlated to paymentAmount and totalPaymentAmount
- Might be some administrative tax on top, or VAT?
- For each case, deduct the penalty from the totalPaymentAmount to find if there is a correlation.

## Event: Send Appeal to Prefecture

Data attributes:
- dismissal: 'G', '#', 'C', 'T', 'E', 'NIL', 'F', 'M', 'U', 'D', 'K', 'N', 'Q', '@', 'V', '3', 'I', 'A', '5', 'B'

## Event: Send Fine

Data attributes:
- expense
Insights:
- For each case, check how totalPaymentAmount paymentAmount expense and amount relate.

## Event: Create Fine

Data attributes:
- amount
- article
- dismissal: 'G', '#', 'C', 'T', 'E', 'NIL', 'F', 'M', 'U', 'D', 'K', 'N', 'Q', '@', 'V', '3', 'I', 'A', '5', 'B'
- points
- totalPaymentAmount
- vehicleClass

Insights:
- article looks numerical but could in fact be categorical (based on the law articles)
- vechicleClass, amount, points, article might be correlated somehow

## Event attribute: dismissal

Is present in 3 events: Create Fine, Send Appeal to Prefecture, Appeal to Judge

## Event attribute: amount

Is present in 2 events: Create Fine, Add Penalty

# Research value

- Hypothesis testing (rejecting the null hypothesis: the target event is executed by chance, the data does not affect the target outcome event) 
- Splitting events according to their frequency (events represent the same concept VS events represent different concepts)
- Splitting data attributes or gathering data attributes according to their link with events (data is independent of the events VS data is bound to a specific event)
- In object centric event logs or event knowledge graphs it can be seen as what?