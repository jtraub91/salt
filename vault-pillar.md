# Salty vault pillar

## __Overview__

Salt's [pillar](https://docs.saltproject.io/en/latest/topics/pillar/) system provides a simple, secure, and flexible way to distribute secrets across a fleet of minions. [Vault](https://www.vaultproject.io/docs/what-is-vault) provides a modern solution for secret storage, access, and auditing.

While salt's current vault integration provide some ability for minions to retrieve secrets from vault in a secure manner, it fails to deliver the simple, flexible, and secure nature of standard salt pillar.

## __Current Implementation__

Salt's current vault integration relies on enabling `peer_run` for the `vault.generate_token` runner function for any minion in need of a vault secret. When a minion requests a secret in vault, it first calls the master to generate a token. The master then generates the token with policies specified in its vault configuration and returns the token to the requesting minion to use while making the request to vault.

### __Problems With Current Implementation__

Let's suppose we want to configure minion policies to be able to have specific minions 

T to be applied across minions is to template the policy by minion id. . Alternatively, policy templated by grains cannot be ied on as a secure solution since a minion can override its grains, potentially evading the intended security policy.


This is particularly ciruitous and unnecessary when utilizing vault as external pillar.

_Caveats_

As it happens, 
_Thoughts_

One thought may be to allow for policy templated by pillar, however, this would still suffer from a similar caveat; pillar can be overrided by a minion with [several functions](https://docs.saltproject.io/en/latest/topics/pillar/#encrypted-pillar-data-on-the-cli).

## __The Proposed Solution__

When integrating vault as external pillar, the vault requests should be made _on the master_ and thus there is no need for `peer_run` to be enabled nor minion access be controlled by vault policy. Instead, all vault secrets to be controlled via salt pillar should be accesible by the master's vault authentication. With this approach, the master would first obtain all secrets in a secure manner before distributing them securely to minions defined by `top` specified in the `ext_pillar` configuration. Consider the following.

```yaml
ext_pillar:
  - vault:
      top:
        base:
          '*':
            - public
            - secret/base
          'I@role:admin':
            - secret
          'G@role:webservers':
            - secret/web
          'I@status:active':
            - secret/live
          ...
```

In the above illustration, the list underneath each target group corresponds to paths in vault. 


## __Alternatives Considered__

Template policy by minion id

```yaml
# /etc/salt/master.d/vault.conf

vault:
  url: https://<vault-url>
  verify: <cert-path>
  auth:
    method: <auth-method>
    ...
  policies:
    - saltstack/minions
    - saltstack/minion/{minion}
  keys:
    - <key-1>
    - <key-2>
    ...
```

With this configuration, a salt minion with minion id `minion-alpha` requesting a token to the master would receive a vault token with attached policies `saltstack/minions` and `saltstack/minion/minion-alpha`. This illustrates that we can achieve a per-minion secret access policy but we would have to explicit policies in vault per-minion. This is cumbersome and unwieldly at scale.

There exists support to template policies by grains. Consider the following configuration.

```yaml
# /etc/salt/master.d/vault.conf
vault:
  url: https://<vault-url>
  verify: <cert-path>
  auth:
    method: <auth-method>
    ...
  policies:
    - saltstack/minions
    - saltstack/minion/{grains[role]}
  keys:
    - <key-1>
    - <key-2>
    ...
```

This configuration allows for a minion's grains to directly influence the policies attached to vault tokens the minion requests. This presents a security concern: a minion can sets it's own grains to potentially inherit an unauthorized policy. 

There is currently no ability for a minion to inherit policy templated by pillar, but even if it did, it would pose a similarity security concern since minion's can override pillar with [several functions](https://docs.saltproject.io/en/latest/topics/pillar/#encrypted-pillar-data-on-the-cli).


Let's suppose we want to securely distribute secrets in vault across a salt minion fleet.


For example, consider the following pillar `top.sls`
```
base:
  'minion1':
    - secret1
  'minion2':
    - secret2
  'minion3':
    - secret3
```
With this structure, secrets in `secret1.sls` get securely distributed to `minion1`, secrets in `secret2.sls` to `minion2` and so on. The secrets are distributed securely to their respective minions and __only__ secrets defined for a given target in `top.sls` will be available for the targeted minions. 

Now let's consider how we may try to achieve this with salt's vault pillar integration
secret path structure
```
pillar
  - secret1
  - secret2
  - secret3
```

one potential solution is to apply a single policy to all minions, e.g.
policy: saltstack/minions
```
path "pillar/*" {
  capabilities = ["read", "list"]
}
```
master conf
```
vault:
  ...
  policies:
    - saltstack/minions
```
_However_, doing so give's all minions access to read everything in the pillar/* path

One solution may be to use the integration's templating ability and apply a unique policy per minion, i.e.
```
vault:
  ...
  policies:
    - saltstack/minion/{minion}
```
with policies
`saltstack/minion/minion1`
```
path "pillar/data/secret1" {
  capabilities = ["read", "list"]
}
```
`saltstack/minion/minion2`
```
path "pillar/data/secret1" {
  capabilities = ["read", "list"]
}
```
This effectively achieves a secure per minion secret transfer as per the original topfile, _but_ it is unwieldly to manage at scale, as a unique policy must be created _per minion_ and modified ongoing to allow/deny new secret paths.

Perhaps you may think that templating by grain get's around this limitation. While it would reduce the amount of policies that need to be created, __it is not secure__. The reason it is not secure is because a clever / nefarious person with access to the minion may override grains, thereby evading the security policy.

One thought I had was to template policy by pillar. For one, this is currently unsupported, and furthermore would _not_ solve the problem because a minion could still override pillar in certain situations, e.g. `salt-call state.apply`



#### References

https://docs.saltproject.io/en/latest/ref/modules/all/salt.modules.vault.html
https://docs.saltproject.io/en/latest/ref/pillar/all/salt.pillar.vault.html
https://docs.saltproject.io/en/latest/ref/runners/all/salt.runners.vault.html
https://docs.saltproject.io/en/latest/ref/sdb/all/salt.sdb.vault.html
https://docs.saltproject.io/en/latest/ref/states/all/salt.states.vault.html