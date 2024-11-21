![Banner Image](banner.png)

# Agentication: Turning Session-Based APIs Into OAuth APIs Programmatically

OAuth is the only solution to delegated authorization for agents that works well today. However, there is an extremely short list of services today that support OAuth. Therefore, in order to increase the secure capabilities of agents, it is important to increase the number of OAuth APIs. That's what Agentication tries to do. From the developer's perspective, they can build client applications on top of LinkedIn/X/JetBlue, for example, as if the real backend APIs were OAuth.

Agentication is a tool designed to seamlessly convert APIs into OAuth APIs using session-captures and a reverse proxy. This allows developers to leverage the security and convenience of OAuth without having to manually refactor their existing session-based API implementations.

## Features

- **Automated Conversion:** Programmatically convert session-based authentication to OAuth.
- **Security Enhancements:** Improve the security of your API by adopting OAuth standards.
- **Easy Integration:** Minimal changes required to integrate with existing APIs.
- **Customizable:** Configure the conversion process to suit your specific needs.
- **Generalizable:** This theoretically works on any session-based APIs

## Improvements

- [ ] Refresh session support
- [ ] Combine proxy into Chrome Extension
- [ ] More expansive client SDK

## Disadvantages

This is just one hypothesis for how to solve delegated authorization of agents. Here are several downsides:

- Requires lots of resource owner support (capture session, many token grants)
- A singular failure point for security
- The sessions can be stored locally, but implementation may require storing session credentials in the cloud.

## Installation

To install Agentication, clone the repository and install the necessary dependencies.

There are three independent pieces to the entire flow (`chrome_extension`, `client`, `proxy`).

They can be used on their own or combined to use the whole demo.
