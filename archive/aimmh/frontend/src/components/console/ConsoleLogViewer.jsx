import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';

export function ConsoleLogViewer({ contextLogs, selectedContextId, onSelectContext }) {
  return (
    <Card>
      <CardHeader className="pb-2"><CardTitle className="text-sm">Captured Context Logs</CardTitle></CardHeader>
      <CardContent className="space-y-2 max-h-[65vh] overflow-y-auto" data-testid="context-log-list">
        {contextLogs.map((log) => (
          <button
            key={log.id}
            onClick={() => onSelectContext(log.id)}
            className={`w-full text-left rounded border p-2 text-xs ${selectedContextId === log.id ? 'border-primary bg-primary/10' : 'border-border bg-muted/20'}`}
            data-testid={`context-log-item-${log.id}`}
          >
            <div className="font-medium truncate">{log.message || 'Untitled context event'}</div>
            <div className="text-[10px] text-muted-foreground truncate">{log.created_at}</div>
          </button>
        ))}
      </CardContent>
    </Card>
  );
}
