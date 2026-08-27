# Northwind Robotics — Security & Device Policy

## Passwords and Authentication

All accounts must use a password of at least 14 characters. Passwords must be
stored in the company password manager, 1Password, and must never be reused
across services. Multi-factor authentication (MFA) is mandatory on all company
systems; SMS-based MFA is not permitted, and employees must use an authenticator
app or a hardware security key.

Passwords do not expire on a fixed schedule. Instead, they must be rotated
immediately if a breach is suspected.

## Device Security

All company laptops must have full-disk encryption enabled (FileVault on macOS,
BitLocker on Windows). Devices must automatically lock after 5 minutes of
inactivity. Employees must not install software from outside the approved
software catalog without IT approval.

Personal devices may be used to access email and chat only if they are enrolled
in the company mobile device management (MDM) system.

## Data Handling

Customer data classified as "Confidential" or "Restricted" must never be copied
to personal devices, personal cloud storage, or removable media such as USB
drives. Restricted data may only be accessed from within the corporate VPN.

## Reporting Incidents

Any suspected security incident — including a lost device, phishing email, or
suspected breach — must be reported to the security team within 1 hour by
emailing security@northwind.example or using the #security-incidents channel.
Do not attempt to investigate a suspected breach yourself.

## Access Reviews

Access to production systems is reviewed quarterly. Any access that has not been
used in 90 days is automatically revoked and must be re-requested.
