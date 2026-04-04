Creates random words to use as a start word. A new start word is selected each
week. Send the start word to a Slack channel, Telegram group or a Signal
group -- somewhere where you and your friends can play along! Everyone uses the
same start word to try to guess the Wordle of the day.

If you're sending the start word to Slack or Telegram, use the `infra_no_ec2.yaml`
CloudFormation template. If you're sending the start word to Signal, use the `infra_signal.yaml`
template which creates an EC2 instance that is needed to send messages to a Signal channel.

## Setting up the workflow

Update the script `update-stack.sh` to add:
- AWS credentials
- EC2 ssh key name

Then update `word_gen.py` to have it send the start word to your preferred destination

Run these commands to set up the stack:

```
update-stack.sh --create-stack
update-stack.sh --upload-word-file
update-stack.sh --deploy-script
```

Add the required params for whichever desination you are sending the messages:

```
update-stack.sh --save-slack-params <webhook url>
# or
update-stack.sh --save-telegram-params <bot token> <chat-id>
```

### Setting up Signal access

If you're sending the start words to a Signal group, log into the EC2 instance to
register your account, giving it access to post messages in your Signal group

```
# Get the EC2 instance ID
update-stack.sh --ec2-instance

# Login via EC2 Instance Connect
> aws ec2-instance-connect ssh --instance-id <instance-id>
ec2> signal-cli link -n "WordleStartWordGen"
```

The command above will display a "sgnl://..." url. Convert this to a QR code. Then
open your Signal mobile app, go to Settings > Linked Devices, and scan the QR code
to link the EC2 instance to your account.

```
Get the destination Signal group ID:
ec2> signal-cli -u +1234567890 listGroups
Id: <group ID> Name: <group name>

# Test that you can send messages to the Signal group
ec2> signal-cli -u +1234567890 send -g <group ID> -m 'Test message'
```

Finally save the Signal account number and group ID in the SSM ParameterStore

```
update-stack.sh --save-signal-params +1234567890 <group-id>
```
