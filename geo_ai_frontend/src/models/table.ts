export interface HeadCell {
  id: string;
  label: string;
  disablePadding?: boolean;
  enabledSort?: boolean;
}

export type Order = "asc" | "desc";
