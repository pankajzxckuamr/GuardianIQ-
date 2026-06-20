import React from 'react';

interface Props {
  value: string;
  onChange: (cron: string) => void;
  timezone: string;
}

export const CronExpressionBuilder: React.FC<Props> = ({ value, onChange, timezone }) => {
  return (
    <div className="flex flex-col gap-2 p-4 border rounded bg-white">
      <label className="text-sm font-medium text-gray-700">Schedule Expression (Cron)</label>
      <input
        type="text"
        className="mt-1 block w-full border-gray-300 rounded-md shadow-sm sm:text-sm"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder="* * * * *"
      />
      <p className="text-xs text-gray-500">Timezone: {timezone}</p>
    </div>
  );
};
