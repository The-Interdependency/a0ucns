import React from 'react';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';

export function ServiceAccountCreateForm({ createForm, setCreateForm, creating, onCreate }) {
  return (
    <div className="space-y-3 rounded-lg border border-border bg-muted/20 p-4" data-testid="service-account-create-section">
      <Label className="text-sm" data-testid="service-account-create-label">Create service account</Label>
      <div className="grid gap-3 md:grid-cols-3">
        <Input
          value={createForm.username}
          onChange={(event) => setCreateForm((prev) => ({ ...prev, username: event.target.value }))}
          placeholder="bot_username"
          data-testid="service-account-create-username-input"
        />
        <Input
          type="password"
          value={createForm.password}
          onChange={(event) => setCreateForm((prev) => ({ ...prev, password: event.target.value }))}
          placeholder="password"
          data-testid="service-account-create-password-input"
        />
        <Input
          value={createForm.label}
          onChange={(event) => setCreateForm((prev) => ({ ...prev, label: event.target.value }))}
          placeholder="label (optional)"
          data-testid="service-account-create-label-input"
        />
      </div>
      <Button
        onClick={onCreate}
        disabled={creating}
        data-testid="service-account-create-submit-button"
      >
        {creating ? 'Creating...' : 'Create Service Account'}
      </Button>
    </div>
  );
}
