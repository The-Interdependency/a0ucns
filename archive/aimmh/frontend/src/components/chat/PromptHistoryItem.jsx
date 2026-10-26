import React from 'react';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { Copy } from 'lucide-react';

export const PromptHistoryItem = ({ prompt, onCopy }) => {
  return (
    <div className="p-1.5 rounded bg-muted/50 text-[10px] space-y-1" data-testid={`prompt-history-item-${prompt.index}`}>
      <div className="flex items-center justify-between gap-1">
        <Badge variant="outline" className="text-[9px] mb-0.5" data-testid={`prompt-history-index-${prompt.index}`}>
          #{prompt.index}
        </Badge>
        <Button
          size="sm"
          variant="ghost"
          className="h-5 w-5 p-0"
          onClick={() => onCopy(prompt.content)}
          data-testid={`prompt-history-copy-btn-${prompt.index}`}
          title="Copy prompt"
        >
          <Copy className="h-3 w-3" />
        </Button>
      </div>
      <div className="text-muted-foreground line-clamp-3" data-testid={`prompt-history-content-${prompt.index}`}>
        {prompt.content}
      </div>
    </div>
  );
};
