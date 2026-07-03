import React from 'react';
import { Copy, KeyRound } from 'lucide-react';
import { toast } from 'sonner';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Switch } from '../ui/switch';

export function ServiceAccountDetails({
  selectedAccount,
  oneTokenPerBot,
  updatingPolicy,
  onPolicyToggle,
  tokenForm,
  setTokenForm,
  issuingToken,
  onIssueToken,
  issuedToken,
  loadingTokens,
  tokens,
  onRevokeToken,
  formatDate,
}) {
  const handleCopyToken = async () => {
    if (!issuedToken) return;
    try {
      await navigator.clipboard.writeText(issuedToken);
      toast.success('Token copied to clipboard');
    } catch {
      toast.error('Could not copy token');
    }
  };

  return (
    <div className="space-y-3 rounded-lg border border-border p-4" data-testid="service-account-token-section">
      <Label className="text-sm" data-testid="service-account-token-section-label">
        {selectedAccount ? `Token management for ${selectedAccount.username}` : 'Select a service account to manage tokens'}
      </Label>

      <div className="flex items-center justify-between rounded-md border border-border bg-muted/20 p-2" data-testid="service-account-policy-row">
        <div>
          <div className="text-xs font-medium" data-testid="service-account-policy-title">One active token per bot</div>
          <div className="text-[10px] text-muted-foreground" data-testid="service-account-policy-help">
            When enabled, issuing a new token auto-revokes any previous active token for that bot.
          </div>
        </div>
        <Switch
          checked={oneTokenPerBot}
          disabled={updatingPolicy}
          onCheckedChange={onPolicyToggle}
          data-testid="service-account-policy-toggle"
        />
      </div>

      <div className="grid gap-3 md:grid-cols-3">
        <Input
          type="password"
          value={tokenForm.password}
          onChange={(event) => setTokenForm((prev) => ({ ...prev, password: event.target.value }))}
          placeholder="service account password"
          disabled={!selectedAccount}
          data-testid="service-account-token-password-input"
        />
        <Input
          type="number"
          min="1"
          max="365"
          value={tokenForm.expiresInDays}
          onChange={(event) => setTokenForm((prev) => ({ ...prev, expiresInDays: event.target.value }))}
          placeholder="Expires in days"
          disabled={!selectedAccount}
          data-testid="service-account-token-expiry-input"
        />
        <Button
          onClick={onIssueToken}
          disabled={!selectedAccount || issuingToken}
          data-testid="service-account-token-issue-button"
        >
          <KeyRound className="mr-1 h-3 w-3" />
          {issuingToken ? 'Issuing...' : 'Issue Token'}
        </Button>
      </div>

      {issuedToken && (
        <div className="rounded border border-emerald-400/30 bg-emerald-400/10 p-3" data-testid="service-account-issued-token-banner">
          <div className="mb-2 text-xs text-emerald-200" data-testid="service-account-issued-token-help">
            Copy this token now. It will not be shown again.
          </div>
          <div className="flex flex-col gap-2 md:flex-row">
            <Input
              value={issuedToken}
              readOnly
              className="font-mono text-xs"
              data-testid="service-account-issued-token-value"
            />
            <Button
              variant="outline"
              onClick={handleCopyToken}
              data-testid="service-account-issued-token-copy-button"
            >
              <Copy className="mr-1 h-3 w-3" /> Copy
            </Button>
          </div>
        </div>
      )}

      <div className="space-y-2" data-testid="service-account-token-list">
        {loadingTokens && (
          <div className="text-xs text-muted-foreground" data-testid="service-account-token-loading">Loading tokens…</div>
        )}
        {!loadingTokens && tokens.length === 0 && (
          <div className="text-xs text-muted-foreground" data-testid="service-account-token-empty">No tokens issued yet.</div>
        )}
        {!loadingTokens && tokens.map((token) => (
          <div
            key={token.id}
            className="flex flex-wrap items-center justify-between gap-2 rounded border border-border bg-muted/20 p-2"
            data-testid={`service-account-token-item-${token.id}`}
          >
            <div className="text-xs" data-testid={`service-account-token-meta-${token.id}`}>
              <div className="font-mono">{token.token_prefix}••••••••</div>
              <div className="text-muted-foreground">
                Expires {formatDate(token.expires_at)} • Last used {formatDate(token.last_used_at)}
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Badge variant={token.revoked ? 'outline' : 'default'} data-testid={`service-account-token-status-${token.id}`}>
                {token.revoked ? 'Revoked' : 'Active'}
              </Badge>
              {!token.revoked && (
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => onRevokeToken(token.id)}
                  data-testid={`service-account-token-revoke-button-${token.id}`}
                >
                  Revoke
                </Button>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
