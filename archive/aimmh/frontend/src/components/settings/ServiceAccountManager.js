import React, { useEffect, useMemo, useState } from 'react';
import axios from 'axios';
import { Bot } from 'lucide-react';
import { toast } from 'sonner';
import { ServiceAccountCreateForm } from './ServiceAccountCreateForm';
import { ServiceAccountList } from './ServiceAccountList';
import { ServiceAccountDetails } from './ServiceAccountDetails';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const formatDate = (value) => {
  if (!value) {
    return '—';
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return '—';
  }
  return date.toLocaleString();
};

export const ServiceAccountManager = () => {
  const [accounts, setAccounts] = useState([]);
  const [tokens, setTokens] = useState([]);
  const [selectedAccountId, setSelectedAccountId] = useState('');
  const [loadingAccounts, setLoadingAccounts] = useState(false);
  const [loadingTokens, setLoadingTokens] = useState(false);
  const [creating, setCreating] = useState(false);
  const [issuingToken, setIssuingToken] = useState(false);
  const [createForm, setCreateForm] = useState({ username: '', password: '', label: '' });
  const [tokenForm, setTokenForm] = useState({ password: '', expiresInDays: '90' });
  const [issuedToken, setIssuedToken] = useState('');
  const [oneTokenPerBot, setOneTokenPerBot] = useState(false);
  const [updatingPolicy, setUpdatingPolicy] = useState(false);

  const selectedAccount = useMemo(
    () => accounts.find((item) => item.id === selectedAccountId),
    [accounts, selectedAccountId]
  );

  const loadServiceAccounts = async () => {
    setLoadingAccounts(true);
    try {
      const response = await axios.get(`${API}/auth/service-accounts`);
      const items = response.data?.items || [];
      setAccounts(items);
      setSelectedAccountId((prev) => {
        if (prev && items.some((item) => item.id === prev)) {
          return prev;
        }
        return items[0]?.id || '';
      });
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to load service accounts');
    } finally {
      setLoadingAccounts(false);
    }
  };

  const loadServiceTokens = async (serviceAccountId) => {
    if (!serviceAccountId) {
      setTokens([]);
      return;
    }
    setLoadingTokens(true);
    try {
      const response = await axios.get(`${API}/auth/service-accounts/${serviceAccountId}/tokens`);
      setTokens(response.data?.items || []);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to load service tokens');
    } finally {
      setLoadingTokens(false);
    }
  };

  const loadServicePolicy = async () => {
    try {
      const response = await axios.get(`${API}/auth/service-account/policy`);
      setOneTokenPerBot(Boolean(response.data?.one_token_per_bot));
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to load service account policy');
    }
  };

  useEffect(() => {
    loadServiceAccounts();
    loadServicePolicy();
  }, []);

  useEffect(() => {
    loadServiceTokens(selectedAccountId);
  }, [selectedAccountId]);

  const handleCreateServiceAccount = async () => {
    if (!createForm.username.trim() || !createForm.password.trim()) {
      toast.error('Username and password are required');
      return;
    }
    setCreating(true);
    try {
      await axios.post(`${API}/auth/service-account/create`, {
        username: createForm.username.trim(),
        password: createForm.password,
        label: createForm.label.trim() || null,
      });
      toast.success('Service account created');
      setCreateForm({ username: '', password: '', label: '' });
      await loadServiceAccounts();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create service account');
    } finally {
      setCreating(false);
    }
  };

  const handleToggleServiceAccount = async (account) => {
    try {
      await axios.patch(`${API}/auth/service-accounts/${account.id}`, {
        active: !account.active,
      });
      toast.success(account.active ? 'Service account disabled' : 'Service account enabled');
      await loadServiceAccounts();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to update service account');
    }
  };

  const handleIssueToken = async () => {
    if (!selectedAccount) {
      toast.error('Select a service account first');
      return;
    }
    if (!tokenForm.password.trim()) {
      toast.error('Enter service account password to issue token');
      return;
    }
    setIssuingToken(true);
    try {
      const response = await axios.post(`${API}/auth/service-account/token`, {
        username: selectedAccount.username,
        password: tokenForm.password,
        expires_in_days: Number(tokenForm.expiresInDays) || 90,
      });
      setIssuedToken(response.data.access_token || '');
      setTokenForm((prev) => ({ ...prev, password: '' }));
      toast.success(oneTokenPerBot ? 'Long-lived token issued (previous active tokens auto-revoked)' : 'Long-lived service token issued');
      await loadServiceTokens(selectedAccount.id);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to issue service token');
    } finally {
      setIssuingToken(false);
    }
  };

  const handleRevokeToken = async (tokenId) => {
    try {
      await axios.post(`${API}/auth/service-account/tokens/${tokenId}/revoke`);
      toast.success('Service token revoked');
      await loadServiceTokens(selectedAccountId);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to revoke token');
    }
  };

  const handlePolicyToggle = async (checked) => {
    const previous = oneTokenPerBot;
    setOneTokenPerBot(checked);
    setUpdatingPolicy(true);
    try {
      await axios.put(`${API}/auth/service-account/policy`, {
        one_token_per_bot: checked,
      });
      toast.success(checked ? 'One-token-per-bot enabled' : 'One-token-per-bot disabled');
    } catch (error) {
      setOneTokenPerBot(previous);
      toast.error(error.response?.data?.detail || 'Failed to update service account policy');
    } finally {
      setUpdatingPolicy(false);
    }
  };

  return (
    <Card className="border-border" data-testid="service-account-manager-card">
      <CardHeader>
        <CardTitle className="flex items-center gap-2" data-testid="service-account-manager-title">
          <Bot className="h-5 w-5" />
          Service Accounts (a0 / API Automation)
        </CardTitle>
        <CardDescription data-testid="service-account-manager-description">
          Create machine users, issue long-lived bearer tokens, and revoke tokens when needed.
        </CardDescription>
      </CardHeader>

      <CardContent className="space-y-6">
        <ServiceAccountCreateForm
          createForm={createForm}
          setCreateForm={setCreateForm}
          creating={creating}
          onCreate={handleCreateServiceAccount}
        />

        <ServiceAccountList
          accounts={accounts}
          selectedAccountId={selectedAccountId}
          setSelectedAccountId={setSelectedAccountId}
          loadingAccounts={loadingAccounts}
          onRefresh={loadServiceAccounts}
          onToggleServiceAccount={handleToggleServiceAccount}
          formatDate={formatDate}
        />

        <ServiceAccountDetails
          selectedAccount={selectedAccount}
          oneTokenPerBot={oneTokenPerBot}
          updatingPolicy={updatingPolicy}
          onPolicyToggle={handlePolicyToggle}
          tokenForm={tokenForm}
          setTokenForm={setTokenForm}
          issuingToken={issuingToken}
          onIssueToken={handleIssueToken}
          issuedToken={issuedToken}
          loadingTokens={loadingTokens}
          tokens={tokens}
          onRevokeToken={handleRevokeToken}
          formatDate={formatDate}
        />
      </CardContent>
    </Card>
  );
};
