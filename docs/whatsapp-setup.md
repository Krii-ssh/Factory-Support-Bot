# Getting WhatsApp working

This guide covers the four credentials, the tunnel that lets Meta reach your
machine, the webhook and what to do each time you restart. Follow it top to
bottom. It takes about 20 to 30 minutes and is free, with no card needed.

Start with the web chat in [setup-guide.md](setup-guide.md) first, because it
proves the rest of the stack works.

---

## First: what the four credentials actually are

Three of them come from Meta. The fourth you make up. That is the part nobody
explains.

| Credential | What it is for | Where it comes from |
|---|---|---|
| `WHATSAPP_PHONE_NUMBER_ID` | **Which number sends.** Meta gives you a free test number, and this is its internal ID | Meta gives it |
| `WHATSAPP_ACCESS_TOKEN` | **Permission to send.** Proves your code is allowed to use that number | Meta gives it |
| `WHATSAPP_APP_SECRET` | **Proves messages really came from Meta.** Without it, anyone who finds your URL can post fake messages and burn your API quota | Meta gives it |
| `WHATSAPP_VERIFY_TOKEN` | **A password you invent.** You type it in two places, and Meta echoes it back once to prove the URL is yours | **You make it up** |

Two directions to keep straight:

- **Outgoing** (your code to WhatsApp) uses the Phone Number ID and the Access
  Token.
- **Incoming** (WhatsApp to your code) needs Meta to reach your computer. That
  needs a public web address, which is what a tunnel is for. The Verify Token and
  App Secret secure that direction.

Treat all four as secrets. Never paste them into an issue, a commit or a chat,
and never commit `.env`.

---

## Step 1: Create the app

1. Go to **developers.facebook.com** and log in with a Facebook account. A
   personal account is fine, and it is not posted anywhere.
2. Choose **My Apps** and then **Create App**.
3. When it asks what you are building, pick the **WhatsApp** use case.
4. Name it anything, for example "Factory Accident Bot".
5. It asks for a Meta Business Account. **Create a new one** if you do not have
   one. Any name will do.

---

## Step 2: Phone Number ID and Access Token (2 of 4)

In the left sidebar choose **WhatsApp**, then **API Setup**. This page has almost
everything.

1. You will see a **test phone number** that Meta gives you free. Under it is
   **Phone number ID**, a long string of digits.
   ⚠️ **Copy the ID, not the phone number.** They look different. The ID is all
   digits and longer.
   This is `WHATSAPP_PHONE_NUMBER_ID`.

2. Near the top is **Temporary access token**. Click to copy it.
   This is `WHATSAPP_ACCESS_TOKEN`.

   ⚠️ **This one expires in 24 hours.** It is fine for testing today. Step 9
   replaces it with a permanent one, and you must do that before any demo.

3. Still on this page, open the **To** field and choose **Manage phone number list**, then add **your own WhatsApp number**. You will get a code on WhatsApp, and you
   enter it.

   Meta only lets the test number message **up to 5 verified numbers**. Add
   yours, and your partner's if they will test too.

4. Click **Send message** on that page. If WhatsApp on your phone pings, the
   outgoing half works.

---

## Step 3: App Secret (3 of 4)

In the left sidebar choose **App settings** and then **Basic**.

Find **App secret**, click **Show** and copy it.

This is `WHATSAPP_APP_SECRET`.

---

## Step 4: Verify Token (4 of 4), which you invent

It is just a password you choose. Use a long random string with no spaces.
Generate one rather than picking something guessable:

```bash
python -c "import secrets; print(secrets.token_urlsafe(24))"
```

This is `WHATSAPP_VERIFY_TOKEN`.

**Write it down.** You type it into two places in Step 7 and they must match
exactly.

---

## Step 5: Put all four in `.env`

Open `.env` in the project folder. The four keys are already there, empty. Fill
them in:

```
WHATSAPP_PHONE_NUMBER_ID=<the digits from step 2>
WHATSAPP_ACCESS_TOKEN=<the token from step 2>
WHATSAPP_APP_SECRET=<the secret from step 3>
WHATSAPP_VERIFY_TOKEN=<the string from step 4>
```

No quotes, and no spaces around `=`.

While you are in there, make sure `GROQ_API_KEY` is set here too, and delete any
old Windows environment variable with the same name. A stale variable overrides
the file. See the troubleshooting section in [setup-guide.md](setup-guide.md).

---

## Step 6: Make your computer reachable

Meta has to be able to call your machine. It cannot reach `localhost`, so you
need a temporary public address.

**Terminal 1: start the server**

```
python -m uvicorn server:app --port 8000
```

Wait for `Application startup complete.`

**Terminal 2: start a tunnel.** Either of these works.

*Cloudflare (no account needed).* Install once with
`winget install --id Cloudflare.cloudflared`, then close the terminal and open a
new one so it is found. Then run:

```
cloudflared tunnel --url http://localhost:8000
```

It prints a box containing an address like
`https://random-words-here.trycloudflare.com`. Copy that **https://** address.

*ngrok (free account, and it can give you a fixed domain).* Download it from
ngrok.com, run the one-time `ngrok config add-authtoken ...` command that they
give you, then run:

```
ngrok http 8000
```

Copy the **https://** address on the `Forwarding` line.

**Leave both terminals running.**

⚠️ With Cloudflare, and with ngrok unless you reserved a domain, the address
changes every time you restart, and you have to update Meta each time. That is
annoying but normal for testing.

---

## Step 7: Tell Meta where to send messages

The webhook path is **`/meta`**. It is not `/webhook`.

In Meta, open **WhatsApp** and then **Configuration**. Depending on the dashboard
version, the same setting sits under **Use cases**, then **Connect with customers
through WhatsApp**, then **Customize**, then **Basic setup**, then
**Step 2. Production setup**, then **Configure Webhooks**. There is no plain
"WhatsApp" item in the sidebar in newer versions, and people hunt for this for
ages.

Next to **Webhook**, click **Edit**:

- **Callback URL:** your tunnel address **plus** the path, for example
  `https://random-words-here.trycloudflare.com/meta`
- **Verify token:** the exact string you invented in Step 4

Click **Verify and save**.

**What happens:** Meta immediately calls your URL and sends the verify token.
Your server checks it matches and echoes the challenge back. The terminal running
the server prints `webhook handshake verified`, and the box closes and saves.

If it fails, it is almost always one of these:

- the server is not running
- the token does not match exactly (check for trailing spaces)
- you forgot `/meta` on the end of the URL

Then, and this bit is easy to miss, under **Webhook fields** click **Manage** and
**subscribe to `messages`**. Without that, verification succeeds but no messages
are ever delivered.

---

## Step 8: Send it a real message

From your own WhatsApp, message the test number. Try:

> the owner is offering us money to sign a paper

You should get the settlement warning with no delay and no model call.

**That is the milestone.** Everything before it was tested against simulated
payloads.

Check that the server is healthy at `<your tunnel address>/health`. You want
`"ok": true`.

---

## Step 9: Permanent token, before any demo

The Step 2 token dies after 24 hours and will fail mid-demo.

1. Go to **business.facebook.com** and open **Business settings**.
2. Choose **Users**, then **System users**, then **Add**. Give it a name and the
   role **Admin**.
3. Choose **Assign assets** and add your app **and** your WhatsApp Business
   Account.
4. Click **Generate new token**, select your app and tick both
   **`whatsapp_business_messaging`** and **`whatsapp_business_management`**.
5. Set the expiry to **Never**.
6. Copy it (it is **shown once**) and replace `WHATSAPP_ACCESS_TOKEN` in `.env`.

Restart the server.

---

## Starting it again after a restart

Everything is already configured. This is just what to run each time you reboot
or close the terminals. **Two windows have to stay open the whole time.**

1. **Window 1:** `python -m uvicorn server:app --port 8000`, and wait for
   `Application startup complete.`
2. **Window 2:** start the tunnel (Step 6) and copy the new address.
3. **Update Meta** with the new address plus `/meta` (Step 7), unless you are
   using a fixed domain.
4. Watch Window 1 for `webhook handshake verified`.
5. Send the test message from Step 8.

---

## If something breaks

| Symptom | Cause and fix |
|---|---|
| Webhook will not verify | Server not running, token mismatch or missing `/meta` on the URL |
| Verified, but no messages arrive | You did not subscribe to the **`messages`** field in Step 7, or the account is unsubscribed from the app (see below) |
| No reply and nothing in the terminal at all | The webhook URL in Meta is stale because the tunnel restarted. Redo Step 7 |
| `190: Invalid OAuth access token` | The token expired (24 hours) or was copied wrong. Go to Step 9 |
| `131030` or "not in allowed list" | Your number is not in the test recipient list. See Step 2.3 |
| Two ticks on your phone but nothing reaches the server | The WhatsApp Business Account has come unsubscribed from the app (see below) |
| Everything worked, now nothing | The tunnel restarted and the URL changed. Update Meta |

### The account that is silently unsubscribed

Subscribing to the `messages` *field* tells Meta **what** to send. Subscribing
the **account to the app** tells it **where**. Without the second, Meta accepts
messages and silently forwards them nowhere. This is invisible in the dashboard
and cost hours the first time.

To fix it, run this in PowerShell, replacing the two placeholders with your own
WhatsApp Business Account ID and a valid access token:

```powershell
$token = "<your access token>"
Invoke-RestMethod -Method Post -Uri "https://graph.facebook.com/v21.0/<your WhatsApp Business Account ID>/subscribed_apps" -Headers @{Authorization="Bearer $token"}
```

You want `success : True`. Do not leave the token in your shell history or in a
saved script.

---

## What this does not need

- ❌ Money
- ❌ A business verification
- ❌ Twilio, which was the dead end because trial accounts cannot send free-form
  text
- ❌ Message templates, because free-form replies are allowed inside the 24-hour
  window that opens when *they* message *you*, which is exactly how this bot is
  used
