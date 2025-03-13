import React from "react";
import { TableCell, TableSortLabel, TableHead, TableRow } from "@mui/material";

import { HeadCell, Order } from "@models/table";

interface EnhancedTableProps {
  headCells: HeadCell[];
  onRequestSort: (property: string) => void;
  order: Order;
  orderBy: string;
}

export const EnhancedTableHead: React.FC<EnhancedTableProps> = ({
  headCells,
  order,
  orderBy,
  onRequestSort,
}) => {
  const createSortHandler = (property: string) => () => {
    onRequestSort(property);
  };

  return (
    <TableHead>
      <TableRow
        sx={{
          ".MuiTableCell-head": {
            fontWeight: "bold",
          },
        }}
      >
        {headCells.map((headCell) => (
          <TableCell
            key={headCell.id}
            padding={headCell.disablePadding ? "none" : "normal"}
            sortDirection={orderBy === headCell.id ? order : false}
          >
            {headCell.enabledSort ? (
              <TableSortLabel
                active={orderBy === headCell.id}
                direction={orderBy === headCell.id ? order : "asc"}
                onClick={createSortHandler(headCell.id)}
              >
                {headCell.label}
              </TableSortLabel>
            ) : (
              headCell.label
            )}
          </TableCell>
        ))}
      </TableRow>
    </TableHead>
  );
};
