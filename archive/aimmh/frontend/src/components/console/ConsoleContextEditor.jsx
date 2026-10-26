import React from 'react';
import { Copy, Save } from 'lucide-react';
import { Button } from '../ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Textarea } from '../ui/textarea';

export function ConsoleContextEditor({
  contextEditor,
  onChange,
  onSave,
  onCopy,
  savingContext,
  selectedContextId,
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm">Editable Prompt Context Payload</CardTitle>
        <CardDescription>Inspect and edit the exact context packet sent with prompts.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-3" data-testid="context-editor-card">
        <div className="grid md:grid-cols-2 gap-3">
          <div className="space-y-1">
            <Label>Context mode</Label>
            <Input value={contextEditor.context_mode} onChange={(e) => onChange('context_mode', e.target.value)} data-testid="context-editor-mode-input" />
          </div>
          <div className="space-y-1">
            <Label>Shared room mode</Label>
            <Input value={contextEditor.shared_room_mode} onChange={(e) => onChange('shared_room_mode', e.target.value)} data-testid="context-editor-shared-mode-input" />
          </div>
        </div>

        <div className="space-y-1">
          <Label>Message</Label>
          <Textarea rows={3} value={contextEditor.message} onChange={(e) => onChange('message', e.target.value)} data-testid="context-editor-message-input" />
        </div>
        <div className="space-y-1">
          <Label>Global context</Label>
          <Textarea rows={3} value={contextEditor.global_context} onChange={(e) => onChange('global_context', e.target.value)} data-testid="context-editor-global-input" />
        </div>
        <div className="space-y-1">
          <Label>Model roles (JSON)</Label>
          <Textarea rows={4} value={contextEditor.model_roles} onChange={(e) => onChange('model_roles', e.target.value)} data-testid="context-editor-roles-input" />
        </div>
        <div className="space-y-1">
          <Label>Per model messages (JSON)</Label>
          <Textarea rows={4} value={contextEditor.per_model_messages} onChange={(e) => onChange('per_model_messages', e.target.value)} data-testid="context-editor-per-model-input" />
        </div>
        <div className="space-y-1">
          <Label>Shared pairs (JSON)</Label>
          <Textarea rows={3} value={contextEditor.shared_pairs} onChange={(e) => onChange('shared_pairs', e.target.value)} data-testid="context-editor-shared-pairs-input" />
        </div>

        <div className="flex flex-wrap gap-2">
          <Button onClick={onSave} disabled={savingContext || !selectedContextId} data-testid="context-editor-save-btn">
            <Save className="h-4 w-4 mr-1" />{savingContext ? 'Saving…' : 'Save context edits'}
          </Button>
          <Button variant="outline" onClick={onCopy} data-testid="context-editor-copy-btn">
            <Copy className="h-4 w-4 mr-1" />Copy payload
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
