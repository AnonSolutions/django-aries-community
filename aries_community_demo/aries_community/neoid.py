def neoid(
    request
    ):
    """
    Create a user account with a managed agent.
    """
    code_verifier = pkce.generate_code_verifier(length=128)
    print('code_verifier->', code_verifier)
    headers = {'Content-type': 'application/x-www-form-urlencoded'}

    client_id = "70e17ae0-30fb-456b-be68-bea32573a9e2"
    code_challenge = pkce.get_code_challenge(code_verifier)
    print('code_challenge->', code_challenge)
    code_challenge_method = "S256"
    redirect_uri = "http://localhost:8000/"
    scope = "single_signature"
    state = "aut"
    login_hint = "45637962049"

    payload = {
        "client_id": "70e17ae0-30fb-456b-be68-bea32573a9e2",
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
        "redirect_uri": "http://localhost:8000/",
        "scope": "single_signature",
        "state": "aut",
        "login_hint": "45637962049"
    }

#    url = "https://neoid.estaleiro.serpro.gov.br/smartcert-api/v0/oauth/authorize/?response_type=code&"
#    response = Response(url, headers=headers, params=payload, verify=False, is_redirect=True)

    url = 'https://neoid.estaleiro.serpro.gov.br/smartcert-api/v0/oauth/authorize/?response_type=code' \
          + '&client_id=' + client_id \
          + '&code_challenge=' + code_challenge \
          + '&code_challenge_method=' + code_challenge_method \
          + '&redirect_uri=' + redirect_uri \
          + '&scope=' + scope \
          + '&state=' + state \
          + '&login_hint=' + login_hint

#    print(url)
#    return redirect(url, headers, verify=False)

    response = redirect(url, headers=headers, verify=False, is_redirect=True)

    return response