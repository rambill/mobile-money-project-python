# Transfer Feature - Mobile Money System

## Overview

The transfer feature allows users to send money from their account to another registered account.

## How It Works

### Server-Side (Atomic Transfer)

1. **Verify sender's PIN**
2. **Check sender account exists**
3. **Check recipient account exists**
4. **Withdraw from sender** (TRANSFER_OUT)
5. **Deposit to recipient** (TRANSFER_IN)
6. **Replicate to all servers**
7. **Rollback if any step fails**

### Client-Side

1. User enters recipient phone number
2. User enters amount to transfer
3. User confirms the transfer
4. Transfer is executed
5. New balance is displayed

## Testing the Feature

### Step 1: Make sure servers are running

```bash
# Terminal 1
python server.py 1

# Terminal 2
python server.py 2

# Terminal 3
python server.py 3
```

### Step 2: Run the transfer test

```bash
python test_transfer.py
```

**Expected output:**
```
============================================================
  TRANSFER FUNCTIONALITY TEST
============================================================

Account 1: 0759123456, PIN: 1111
Account 2: 0758123456, PIN: 2222
------------------------------------------------------------

1. Registering Account 1...
   ✓ Account 1 registered

2. Registering Account 2...
   ✓ Account 2 registered

3. Depositing 10000 to Account 1...
   ✓ Deposit successful, balance: 10000.0

4. Checking balances before transfer...
   Account 1 balance: 10000.0
   Account 2 balance: 0.0

5. Transferring 3000 from Account 1 to Account 2...
   ✓ Transfer successful!
   Account 1 new balance: 7000.0

6. Waiting 1 second for replication...

7. Checking balances after transfer...
   Account 1 balance: 7000.0
   ✓ Correct! (10000 - 3000 = 7000)
   Account 2 balance: 3000.0
   ✓ Correct! (0 + 3000 = 3000)

8. Testing insufficient balance...
   ✓ Correctly rejected insufficient balance

9. Testing invalid recipient...
   ✓ Correctly rejected invalid recipient

============================================================
  🎉 TRANSFER TESTS COMPLETE!
============================================================
```

### Step 3: Use in the client

```bash
python client.py
```

## Usage Example

### Scenario: Alice sends money to Bob

**Alice's Account:** 0759111111, PIN: 1111  
**Bob's Account:** 0759222222, PIN: 2222

#### Step 1: Alice registers and deposits

```
Select option: 1
Phone: 0759111111
PIN: 1111

Select option: 4
Amount: 10000
✓ Success, New balance: UGX 10,000.00
```

#### Step 2: Bob registers

```
Select option: 0  (Exit)

# Start client again
python client.py

Select option: 1
Phone: 0759222222
PIN: 2222
```

#### Step 3: Alice transfers to Bob

```
Select option: 0  (Exit)

# Start client again
python client.py

Select option: 2  (Login)
Phone: 0759111111
PIN: 1111

Select option: 6  (Transfer money)
Recipient phone: 0759222222
Amount: 3000

Transfer UGX 3,000.00 to 0759222222?
Type 'yes' to confirm: yes

✓ Transfer successful
  Your new balance: UGX 7,000.00
```

#### Step 4: Bob checks his balance

```
Select option: 0  (Exit)

# Start client again
python client.py

Select option: 2  (Login)
Phone: 0759222222
PIN: 2222

Select option: 3  (Check balance)
✓ Balance: UGX 3,000.00
```

## Features

### ✅ Validation

- **PIN verification** - Sender must provide correct PIN
- **Account existence** - Both sender and recipient must exist
- **Sufficient balance** - Sender must have enough money
- **Self-transfer prevention** - Cannot transfer to yourself

### ✅ Atomicity

- **All-or-nothing** - Either both withdraw and deposit succeed, or neither
- **Automatic rollback** - If deposit fails, withdrawal is reversed
- **Consistent state** - Accounts always in valid state

### ✅ Replication

- **Distributed** - Transfer replicates to all servers
- **Consistent** - All servers see the same transfer
- **Reliable** - Works even if some servers are slow

### ✅ Transaction Types

The system tracks different transaction types:
- `TRANSFER_OUT` - Money sent from your account
- `TRANSFER_IN` - Money received in your account
- `TRANSFER_ROLLBACK` - Transfer was reversed (rare)

## Error Handling

### Invalid PIN
```
✗ Invalid PIN
```
**Solution:** Check your PIN and try again

### Recipient not found
```
✗ Recipient account not found
```
**Solution:** Verify the recipient's phone number

### Insufficient balance
```
✗ Insufficient balance
```
**Solution:** Deposit more money or transfer a smaller amount

### Transfer to self
```
Cannot transfer to yourself!
```
**Solution:** Enter a different recipient phone number

## Menu Options

The client menu now includes:

```
1. Register new account
2. Login
3. Check balance
4. Deposit money
5. Withdraw money
6. Transfer money          ← NEW!
7. Switch server
8. Show server status
0. Exit
```

## Technical Details

### Protocol

**Request:**
```
REQ|<id>|TRANSFER|<from_phone>|<pin>|<to_phone>|<amount>
```

**Response (Success):**
```
RES|<id>|OK|Transfer successful|<sender_new_balance>|<vector_clock>
```

**Response (Error):**
```
RES|<id>|ERR|<error_message>|<sender_balance>|<vector_clock>
```

### Database

Transfers create two transaction records:

**Sender's transaction:**
```sql
INSERT INTO transactions 
  (phone, type, amount, balance_after, ...)
VALUES 
  ('0759111111', 'TRANSFER_OUT', -3000, 7000, ...)
```

**Recipient's transaction:**
```sql
INSERT INTO transactions 
  (phone, type, amount, balance_after, ...)
VALUES 
  ('0759222222', 'TRANSFER_IN', 3000, 3000, ...)
```

### Replication

Transfer operation replicates as:
```json
{
  "command": "TRANSFER",
  "from_phone": "0759111111",
  "to_phone": "0759222222",
  "amount": 3000,
  "sender_vc": "{...}",
  "recipient_vc": "{...}"
}
```

## Summary

✅ **Transfer feature is fully implemented**  
✅ **Atomic operations** - All-or-nothing  
✅ **Validated** - PIN, accounts, balance checked  
✅ **Replicated** - Works across all servers  
✅ **Tested** - Comprehensive test suite  

**You can now transfer money between accounts!** 🎉

## Next Steps

1. Run `python test_transfer.py` to verify
2. Use `python client.py` to try transfers
3. Create multiple accounts and transfer between them
4. Check transaction history in the database

Enjoy your enhanced mobile money system!
