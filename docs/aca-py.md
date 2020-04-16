## Server ##
GET	/plugins	Fetch the list of loaded plugins
GET	/status		Fetch the server status
POST	/status/reset	Reset statistics 
GET	/features	Query supported feature

## Connections ##
GET	/connections	Query agent-to-agent connections
GET	/connections/{id}	Fetch a single connection record
POST	/connections/create-static	Create a new static connection
POST	/connections/create-invitation	Create a new connection invitation
POST	/connections/receive-invitation	Receive a new connection invitation
POST	/connections/{id}/accept-invitation	Accept a stored connection invitation
POST	/connections/{id}/accept-request	Accept a stored connection request
POST	/connections/{id}/establish-inbound/{ref_id}	Assign another connection as the inbound connection
POST	/connections/{id}/remove	Remove an existing connection record

## action-menu ##
POST	/action-menu/{id}/close	Close the active menu associated with a connection
POST	/action-menu/{id}/fetch	Fetch the active menu
POST	/action-menu/{id}/perform	Perform an action associated with the active menu
POST	/action-menu/{id}​/request	Request the active menu
POST	/connections/{id}/send-menu	Send an action menu to a connection

## basicmessage ##
POST	/connections/{id}/send-message	Send a basic message to a connection	issue-credential

## issue-credential ##
GET	/issue-credential/mime-types/{credential_id}	Get attribute MIME types from wallet
GET	/issue-credential/records	Fetch all credential exchange records
GET	/issue-credential/records/{cred_ex_id}	Fetch a single credential exchange record
POST	/issue-credential/send	Send holder a credential, automating entire flow
POST	/issue-credential/send-proposal	Send issuer a credential proposal
POST	/issue-credential/send-offer	Send holder a credential offer, independent of any proposal with preview
POST	/issue-credential/records/{cred_ex_id}/send-offer	Send holder a credential offer in reference to a proposal with preview
POST	/issue-credential/records/{cred_ex_id}/send-request	Send issuer a credential request
POST	/issue-credential/records/{cred_ex_id}/issue	Send holder a credential
POST	/issue-credential/records/{cred_ex_id}/store	Store a received credential
POST	/issue-credential/revoke	Revoke an issued credential
POST	/issue-credential/publish-revocations	Publish pending revocations to ledger
POST	/issue-credential/records/{cred_ex_id}/remove	Remove an existing credential exchange record
POST	/issue-credential/records/{cred_ex_id}/problem-report	Send a problem report for credential exchange


## present-proof ##
GET	/present-proof/records	Fetch all present-proof exchange records
GET	/present-proof/records/{pres_ex_id}	Fetch a single presentation exchange record
GET	/present-proof/records/{pres_ex_id}/credentials	Fetch credentials for a presentation request from wallet
GET	/present-proof/records/{pres_ex_id}/credentials/{referent}	Fetch credentials for a presentation request from wallet
POST	/present-proof/send-proposal	Sends a presentation proposal
POST	/present-proof/create-request	Creates a presentation request not bound to any proposal or existing connection
POST	/present-proof/send-request	Sends a free presentation request not bound to any proposal
POST	/present-proof/records/{pres_ex_id}/send-request	Sends a presentation request in reference to a proposal
POST	/present-proof/records/{pres_ex_id}/send-presentation	Sends a proof presentation
POST	/present-proof/records/{pres_ex_id}/verify-presentation	Verify a received presentation
POST	/present-proof/records/{pres_ex_id}/remove	Remove an existing presentation exchange record

## trustping ##
POST	/connections/{id}/send-ping	Send a trust ping to a connection

## credentials ##
GET	/credential/{id}	Fetch a credential from wallet by id
POST	/credential/{id}/remove	Remove a credential from the wallet by id
GET	/credentials	Fetch credentials from wallet	credential_exchange 

## *DEPRECATED* ##
GET	/credential_exchange	Fetch all credential exchange records
GET	/credential_exchange/{id}	Fetch a single credential exchange record
POST	/credential_exchange/send	Sends a credential and automates the entire flow
POST	/credential_exchange/send-offer	Sends a credential offer
POST	/credential_exchange/{id}/send-request	Sends a credential request
POST	/credential_exchange/{id}/issue	Sends a credential
POST	/credential_exchange/{id}/store	Stores a received credential
POST	/credential_exchange/{id}/problem_report	Send a problem report for credential exchange
POST	/credential_exchange/{id}/remove	Remove an existing credential exchange record

## ledger ##
POST	/ledger/register-nym	Send a NYM registration to the ledger.
GET	/ledger/did-verkey	Get the verkey for a DID from the ledger.
GET	/ledger/did-endpoint	Get the endpoint for a DID from the ledger.
GET	/ledger/taa	Fetch the current transaction author agreement, if any
POST	/ledger/taa/accept	Accept the transaction author agreement

## credential-definition ##
POST	/credential-definitions	Sends a credential definition to the ledger
GET	/credential-definitions/created	Search for matching credential definitions that agent originated
GET	/credential-definitions/{id}	Gets a credential definition from the ledger

## schema ##
POST	/schemas	Sends a schema to the ledger
GET	/schemas/created	Search for matching schema that agent originated
GET	/schemas/{id}	Gets a schema from the ledger

## revocation ##
POST	/revocation/create-registry	Creates a new revocation registry
GET	/revocation/registry/{id}	Get revocation registry by credential definition id
PATCH	/revocation/registry/{id}	Update revocation registry with new public URI to the tails file.
GET	/revocation/active-registry/{cred_def_id}	Get an active revocation registry by credential definition id
GET	/revocation/registry/{id}/tails-file	Download the tails file of revocation registry
POST	/revocation/registry/{id}/publish	Publish a given revocation registry

## wallet ##
GET	/wallet/did	List wallet DIDs
POST	/wallet/did/create	Create a local DID
GET	/wallet/did/public	Fetch the current public DID
POST	/wallet/did/public	Assign the current public DID
GET	/wallet/tag-policy/{id}	Get the tagging policy for a credential definition
POST	/wallet/tag-policy/{id}	Set the tagging policy for a credential definition
