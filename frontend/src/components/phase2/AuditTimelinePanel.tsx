import React, { useEffect, useState } from 'react';

interface Props {
  entityType: string;
  entityId: string;
}

export const AuditTimelinePanel: React.FC<Props> = ({ entityType, entityId }) => {
  const [events, setEvents] = useState<any[]>([]);

  useEffect(() => {
    fetch(`/api/v1/audit/events?entity_type=${entityType}&entity_id=${entityId}`)
      .then(r => r.json())
      .then(d => {
        if (d.success) setEvents(d.data.items || []);
      })
      .catch(console.error);
  }, [entityType, entityId]);

  return (
    <div className="flow-root">
      <ul className="-mb-8">
        {events.map((ev, idx) => (
          <li key={ev.id}>
            <div className="relative pb-8">
              {idx !== events.length - 1 && (
                <span className="absolute top-4 left-4 -ml-px h-full w-0.5 bg-gray-200" aria-hidden="true" />
              )}
              <div className="relative flex space-x-3">
                <div>
                  <span className="h-8 w-8 rounded-full bg-gray-400 flex items-center justify-center ring-8 ring-white">
                    <span className="text-white text-xs">{ev.action_type?.charAt(0) || 'E'}</span>
                  </span>
                </div>
                <div className="flex min-w-0 flex-1 justify-between space-x-4 pt-1.5">
                  <div>
                    <p className="text-sm text-gray-500">{ev.event_summary}</p>
                  </div>
                  <div className="whitespace-nowrap text-right text-sm text-gray-500">
                    <time dateTime={ev.created_at}>{new Date(ev.created_at).toLocaleString()}</time>
                  </div>
                </div>
              </div>
            </div>
          </li>
        ))}
        {events.length === 0 && <p className="text-sm text-gray-500 py-4">No audit history found.</p>}
      </ul>
    </div>
  );
};
