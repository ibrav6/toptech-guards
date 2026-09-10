import type { ReactNode } from 'react';
export type TableColumn<T> = { key: string; heading: string; render: (row: T) => ReactNode };
export function DataTable<T>({ caption, columns, rows, rowKey }: { caption: string; columns: TableColumn<T>[]; rows: T[]; rowKey: (row: T) => string }) {
  return <div className="tt-table-wrap" tabIndex={0} role="region" aria-label={caption}><table className="tt-table"><caption>{caption}</caption><thead><tr>{columns.map(c => <th scope="col" key={c.key}>{c.heading}</th>)}</tr></thead><tbody>{rows.map(row => <tr key={rowKey(row)}>{columns.map(c => <td key={c.key}>{c.render(row)}</td>)}</tr>)}</tbody></table></div>;
}
