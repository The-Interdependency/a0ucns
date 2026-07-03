import React from 'react';
import { RefreshCw, ShieldAlert, ShieldCheck } from 'lucide-react';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { Label } from '../ui/label';

export function ServiceAccountList({
  accounts,
  selectedAccountId,
  setSelectedAccountId,
  loadingAccounts,
  onRefresh,
  onToggleServiceAccount,
  formatDate,
}) {
  return (
    <div className="space-y-3" data-testid="service-account-list-section">
      <div className="flex items-center justify-between">
        <Label className="text-sm" data-testid="service-account-list-label">Your service accounts</Label>
        <Button
          variant="outline"
          size="sm"
          onClick={onRefresh}
          disabled={loadingAccounts}
          data-testid="service-account-refresh-button"
        >
          <RefreshCw className={`mr-1 h-3 w-3 ${loadingAccounts ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      {accounts.length === 0 && (
        <div className="rounded border border-dashed border-border p-3 text-xs text-muted-foreground" data-testid="service-account-empty-state">
          No service accounts yet.
        </div>
      )}

      {accounts.map((account) => {
        const isSelected = selectedAccountId === account.id;
        return (
          <div
            key={account.id}
            className={`rounded-lg border p-3 ${isSelected ? 'border-primary/60 bg-primary/5' : 'border-border bg-card'}`}
            data-testid={`service-account-item-${account.id}`}
          >
            <div className="flex flex-wrap items-center justify-between gap-2">
              <button
                type="button"
                className="text-left"
                onClick={() => setSelectedAccountId(account.id)}
                data-testid={`service-account-select-button-${account.id}`}
              >
                <div className="text-sm font-semibold" data-testid={`service-account-username-${account.id}`}>{account.username}</div>
                <div className="text-xs text-muted-foreground" data-testid={`service-account-meta-${account.id}`}>
                  {account.label || 'No label'} • Created {formatDate(account.created_at)}
                </div>
              </button>
              <div className="flex items-center gap-2">
                <Badge
                  variant={account.active ? 'default' : 'outline'}
                  data-testid={`service-account-status-${account.id}`}
                >
                  {account.active ? 'Active' : 'Disabled'}
                </Badge>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => onToggleServiceAccount(account)}
                  data-testid={`service-account-toggle-button-${account.id}`}
                >
                  {account.active ? (
                    <><ShieldAlert className="mr-1 h-3 w-3" /> Disable</>
                  ) : (
                    <><ShieldCheck className="mr-1 h-3 w-3" /> Enable</>
                  )}
                </Button>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
