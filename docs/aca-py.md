## Server ##  
GET	  /plugins	Fetch the list of loaded plugins  
GET	  /status		    Fetch the server status  
POST	/status/reset	Reset statistics  
GET	  /features	    Query supported feature  

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
