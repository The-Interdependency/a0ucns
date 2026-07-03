import { useCallback, useEffect, useMemo, useState } from 'react';
import { toast } from 'sonner';
import { hubApi } from '../lib/hubApi';

export function useHubWorkspace() {
  const [models, setModels] = useState([]);
  const [options, setOptions] = useState(null);
  const [instances, setInstances] = useState([]);
  const [groups, setGroups] = useState([]);
  const [runs, setRuns] = useState([]);
  const [selectedRunId, setSelectedRunId] = useState('');
  const [selectedRun, setSelectedRun] = useState(null);
  const [includeArchivedInstances, setIncludeArchivedInstances] = useState(false);
  const [includeArchivedGroups, setIncludeArchivedGroups] = useState(false);
  const [includeArchivedRuns, setIncludeArchivedRuns] = useState(false);
  const [loading, setLoading] = useState(true);
  const [busyKey, setBusyKey] = useState('');

  const refreshCore = useCallback(async (instanceArchiveFlag = includeArchivedInstances, groupArchiveFlag = includeArchivedGroups) => {
    const [modelsRes, optionsRes, instancesRes, groupsRes, runsRes] = await Promise.all([
      hubApi.getModels(),
      hubApi.getOptions(),
      hubApi.getInstances(instanceArchiveFlag),
      hubApi.getGroups(groupArchiveFlag),
      hubApi.getRuns(),
    ]);

    setModels(modelsRes?.developers || []);
    setOptions(optionsRes);
    setInstances(instancesRes?.instances || []);
    setGroups(groupsRes?.groups || []);
    setRuns(runsRes?.runs || []);

    const nextSelectedRunId = selectedRunId || runsRes?.runs?.[0]?.run_id || '';
    setSelectedRunId(nextSelectedRunId);
    if (nextSelectedRunId) {
      const detail = await hubApi.getRunDetail(nextSelectedRunId);
      setSelectedRun(detail);
    } else {
      setSelectedRun(null);
    }
  }, [includeArchivedGroups, includeArchivedInstances, selectedRunId]);

  useEffect(() => {
    let active = true;
    (async () => {
      try {
        setLoading(true);
        await refreshCore();
      } catch (error) {
        if (active) toast.error(error.message || 'Failed to load AIMMH hub');
      } finally {
        if (active) setLoading(false);
      }
    })();
    return () => { active = false; };
  }, [refreshCore]);

  useEffect(() => {
    if (!selectedRunId) {
      setSelectedRun(null);
      return;
    }
    let active = true;
    (async () => {
      try {
        const detail = await hubApi.getRunDetail(selectedRunId);
        if (active) setSelectedRun(detail);
      } catch (error) {
        if (active) toast.error(error.message || 'Failed to load run detail');
      }
    })();
    return () => { active = false; };
  }, [selectedRunId]);

  const runTask = useCallback(async (key, task, successMessage) => {
    try {
      setBusyKey(key);
      const result = await task();
      if (successMessage) toast.success(successMessage);
      return result;
    } catch (error) {
      toast.error(error.message || 'Request failed');
      throw error;
    } finally {
      setBusyKey('');
    }
  }, []);

  const reloadInstances = useCallback(async (flag = includeArchivedInstances) => {
    const res = await hubApi.getInstances(flag);
    setInstances(res?.instances || []);
  }, [includeArchivedInstances]);

  const reloadGroups = useCallback(async (flag = includeArchivedGroups) => {
    const res = await hubApi.getGroups(flag);
    setGroups(res?.groups || []);
  }, [includeArchivedGroups]);

  const reloadRuns = useCallback(async (flag = includeArchivedRuns) => {
    const res = await hubApi.getRuns(flag);
    const nextRuns = res?.runs || [];
    setRuns(nextRuns);
    return nextRuns;
  }, [includeArchivedRuns]);

  useEffect(() => {
    reloadInstances(includeArchivedInstances).catch(() => {});
  }, [includeArchivedInstances, reloadInstances]);

  useEffect(() => {
    reloadGroups(includeArchivedGroups).catch(() => {});
  }, [includeArchivedGroups, reloadGroups]);

  useEffect(() => {
    reloadRuns(includeArchivedRuns).catch(() => {});
  }, [includeArchivedRuns, reloadRuns]);

  const createInstance = useCallback(async (payload) => runTask('create-instance', async () => {
    await hubApi.createInstance(payload);
    await reloadInstances();
  }, 'Instance created'), [reloadInstances, runTask]);

  const updateInstance = useCallback(async (instanceId, payload) => runTask(`update-instance-${instanceId}`, async () => {
    await hubApi.updateInstance(instanceId, payload);
    await reloadInstances();
  }, 'Instance updated'), [reloadInstances, runTask]);

  const toggleInstanceArchive = useCallback(async (instance) => runTask(`toggle-instance-${instance.instance_id}`, async () => {
    if (instance.archived) await hubApi.unarchiveInstance(instance.instance_id);
    else await hubApi.archiveInstance(instance.instance_id);
    await reloadInstances();
  }, instance.archived ? 'Instance restored' : 'Instance archived'), [reloadInstances, runTask]);

  const deleteArchivedInstance = useCallback(async (instanceId) => runTask(`delete-instance-${instanceId}`, async () => {
    await hubApi.deleteInstance(instanceId);
    await reloadInstances();
  }, 'Archived instance deleted'), [reloadInstances, runTask]);

  const archiveManyInstances = useCallback(async (instanceIds) => runTask('archive-many-instances', async () => {
    const targets = instances.filter((item) => instanceIds.includes(item.instance_id) && !item.archived);
    if (targets.length === 0) return;
    await Promise.all(targets.map((instance) => hubApi.archiveInstance(instance.instance_id)));
    await reloadInstances();
  }, 'Selected instances archived'), [instances, reloadInstances, runTask]);

  const restoreManyInstances = useCallback(async (instanceIds) => runTask('restore-many-instances', async () => {
    const targets = instances.filter((item) => instanceIds.includes(item.instance_id) && item.archived);
    if (targets.length === 0) return;
    await Promise.all(targets.map((instance) => hubApi.unarchiveInstance(instance.instance_id)));
    await reloadInstances();
  }, 'Selected instances restored'), [instances, reloadInstances, runTask]);

  const deleteManyArchivedInstances = useCallback(async (instanceIds) => runTask('delete-many-instances', async () => {
    const targets = instances.filter((item) => instanceIds.includes(item.instance_id) && item.archived);
    if (targets.length === 0) return;
    await Promise.all(targets.map((instance) => hubApi.deleteInstance(instance.instance_id)));
    await reloadInstances();
  }, 'Selected archived instances deleted'), [instances, reloadInstances, runTask]);

  const fetchInstanceHistory = useCallback((instanceId) => hubApi.getInstanceHistory(instanceId), []);

  const createGroup = useCallback(async (payload) => runTask('create-group', async () => {
    await hubApi.createGroup(payload);
    await reloadGroups();
  }, 'Group saved'), [reloadGroups, runTask]);

  const updateGroup = useCallback(async (groupId, payload) => runTask(`update-group-${groupId}`, async () => {
    await hubApi.updateGroup(groupId, payload);
    await reloadGroups();
  }, 'Group updated'), [reloadGroups, runTask]);

  const toggleGroupArchive = useCallback(async (group) => runTask(`toggle-group-${group.group_id}`, async () => {
    if (group.archived) await hubApi.unarchiveGroup(group.group_id);
    else await hubApi.archiveGroup(group.group_id);
    await reloadGroups();
  }, group.archived ? 'Group restored' : 'Group archived'), [reloadGroups, runTask]);

  const createRun = useCallback(async (payload) => runTask('create-run', async () => {
    const detail = await hubApi.createRun(payload);
    const nextRuns = await reloadRuns();
    setSelectedRun(detail);
    setSelectedRunId(detail.run_id);
    if (!nextRuns.find((item) => item.run_id === detail.run_id)) {
      setRuns((prev) => [detail, ...prev]);
    }
    return detail;
  }, 'Pipeline executed'), [reloadRuns, runTask]);

  const toggleRunArchive = useCallback(async (run) => runTask(`toggle-run-${run.run_id}`, async () => {
    if (run.archived) await hubApi.unarchiveRun(run.run_id);
    else await hubApi.archiveRun(run.run_id);
    const nextRuns = await reloadRuns();
    if (!nextRuns.find((item) => item.run_id === selectedRunId)) {
      setSelectedRunId(nextRuns[0]?.run_id || '');
    }
  }, run.archived ? 'Run restored' : 'Run archived'), [reloadRuns, runTask, selectedRunId]);

  const deleteArchivedRun = useCallback(async (runId) => runTask(`delete-run-${runId}`, async () => {
    await hubApi.deleteRun(runId);
    const nextRuns = await reloadRuns();
    if (selectedRunId === runId) {
      setSelectedRunId(nextRuns[0]?.run_id || '');
    }
  }, 'Archived run deleted'), [reloadRuns, runTask, selectedRunId]);

  const modelOptions = useMemo(() => models.flatMap((developer) =>
    (developer.models || []).map((model) => ({
      value: model.model_id,
      label: `${developer.name} · ${model.display_name || model.model_id}`,
    }))
  ), [models]);

  const sourceOptions = useMemo(() => ([
    ...instances.filter((item) => !item.archived).map((item) => ({
      source_type: 'instance',
      source_id: item.instance_id,
      label: `${item.name} · ${item.model_id}`,
    })),
    ...groups.filter((item) => !item.archived).map((item) => ({
      source_type: 'group',
      source_id: item.group_id,
      label: `${item.name} · group`,
    })),
  ]), [groups, instances]);

  const exportInventory = useCallback(() => {
    const payload = {
      exported_at: new Date().toISOString(),
      developers: models,
      instances,
      groups,
    };
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `aimmh-inventory-${new Date().toISOString().slice(0, 19).replace(/[:T]/g, '-')}.json`;
    link.click();
    URL.revokeObjectURL(url);
    toast.success('Inventory exported');
  }, [groups, instances, models]);

  return {
    models,
    options,
    instances,
    groups,
    runs,
    selectedRun,
    selectedRunId,
    setSelectedRunId,
    includeArchivedInstances,
    setIncludeArchivedInstances,
    includeArchivedGroups,
    setIncludeArchivedGroups,
    includeArchivedRuns,
    setIncludeArchivedRuns,
    loading,
    busyKey,
    modelOptions,
    sourceOptions,
    refreshCore,
    reloadInstances,
    reloadGroups,
    reloadRuns,
    createInstance,
    updateInstance,
    toggleInstanceArchive,
    deleteArchivedInstance,
    archiveManyInstances,
    restoreManyInstances,
    deleteManyArchivedInstances,
    fetchInstanceHistory,
    createGroup,
    updateGroup,
    toggleGroupArchive,
    createRun,
    toggleRunArchive,
    deleteArchivedRun,
    exportInventory,
  };
}
