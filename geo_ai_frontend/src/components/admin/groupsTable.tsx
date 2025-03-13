import React, { useState, ChangeEvent, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { useDebounce } from "use-debounce";
import {
  Box,
  IconButton,
  InputAdornment,
  Table,
  TableBody,
  TableCell,
  TableFooter,
  TablePagination,
  TableRow,
  TextField,
  Typography,
} from "@mui/material";
import SearchIcon from "@mui/icons-material/Search";
import EditIcon from "@mui/icons-material/Edit";

import { Group } from "@models/user";
import { useAdminStore } from "@store/admin.store";
import { EnhancedTableHead } from "@components/shared/enhancedTableHead";
import { HeadCell } from "@models/table";
import noProjectsUrl from "@assets/no_projects.png";

export const GroupsTable: React.FC = () => {
  const { t } = useTranslation();
  const {
    groups,
    groupsPaginationData,
    groupsFilterSortData,
    getGroups,
    setGroupsPaginationData,
    setGroupsFilterSortData,
  } = useAdminStore();

  const [search, setSearch] = useState("");
  const [debouncedSearch] = useDebounce(search, 500);

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedGroup, setSelectedGroup] = useState<Group>();

  useEffect(() => {
    getGroups({
      page: groupsPaginationData.page,
      limit: groupsPaginationData.limit,
      ...groupsFilterSortData,
    });
  }, []);

  useEffect(() => {
    if (debouncedSearch !== (groupsFilterSortData.search || "")) {
      setGroupsFilterSortData({
        ...groupsFilterSortData,
        search: debouncedSearch === "" ? undefined : debouncedSearch,
      });
    }
  }, [debouncedSearch]);

  const headCells: HeadCell[] = [
    {
      id: "name",
      label: t("admin.groupName"),
      enabledSort: true,
    },
    {
      id: "users",
      label: t("general.users"),
    },
    {
      id: "created_at",
      label: t("admin.date"),
      enabledSort: true,
    },
    {
      id: "action",
      label: t("admin.action"),
    },
  ];

  const handleRequestSort = (key: string) => {
    const isSameField = groupsFilterSortData.sort === key;
    setGroupsFilterSortData({
      ...groupsFilterSortData,
      sort: key as keyof Group,
      reverse: isSameField ? !groupsFilterSortData.reverse : false,
    });
  };

  const onSearchChange = (e: ChangeEvent<HTMLInputElement>) => {
    setSearch(e.target.value);
  };

  const onPageChange = (page: number) => {
    setGroupsPaginationData({
      ...groupsPaginationData,
      page: page + 1,
    });
  };

  const onRowsPerPageChange = (
    e: ChangeEvent<HTMLTextAreaElement | HTMLInputElement>
  ) => {
    const limit = +e.target.value;

    setGroupsPaginationData({
      ...groupsPaginationData,
      limit,
    });
  };

  const onEditGroup = (group: Group) => {
    setSelectedGroup(group);
    setIsModalOpen(true);

    console.log(selectedGroup);
    console.log(isModalOpen);
  };

  return (
    <>
      <Box component="div" sx={{ display: "flex", mt: 2, gap: 2 }} dir="ltr">
        <TextField
          label={t("general.search")}
          variant="outlined"
          size="small"
          value={search}
          onChange={onSearchChange}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon />
              </InputAdornment>
            ),
          }}
          sx={{ width: 300 }}
          id="user-search"
        />
      </Box>
      {!groupsPaginationData.total ? (
        <Box
          component="div"
          sx={{
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            mt: 16,
            gap: 2,
          }}
        >
          <img width="190" src={noProjectsUrl} />
          <Typography variant="h4">{t("admin.noGroups")}</Typography>
        </Box>
      ) : (
        <Table sx={{ mt: 2 }} dir="ltr">
          <EnhancedTableHead
            headCells={headCells}
            order={groupsFilterSortData.reverse ? "asc" : "desc"}
            orderBy={groupsFilterSortData.sort || ""}
            onRequestSort={handleRequestSort}
          />
          <TableBody>
            {groups.map((group) => (
              <TableRow
                key={group.id}
                sx={{ "&:last-child td, &:last-child th": { border: 0 } }}
              >
                <TableCell sx={{ maxWidth: 300 }}>
                  <Typography
                    variant="body1"
                    sx={{ fontWeight: "bold", wordWrap: "break-word" }}
                  >
                    {group.name}
                  </Typography>
                </TableCell>
                <TableCell>list of users</TableCell>
                <TableCell>
                  {t("intlDateTime", {
                    val: new Date(group.created_at),
                    formatParams: {
                      val: {
                        year: "numeric",
                        month: "long",
                        day: "numeric",
                        hour: "numeric",
                        minute: "numeric",
                      },
                    },
                  })}
                </TableCell>
                <TableCell>
                  <Box component="div" sx={{ display: "flex", gap: 1 }}>
                    <IconButton
                      onClick={() => onEditGroup(group)}
                      id={`user-${group.id}-edit-button`}
                    >
                      <EditIcon />
                    </IconButton>
                  </Box>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
          <TableFooter>
            <TableRow>
              <TablePagination
                count={groupsPaginationData.total}
                page={groupsPaginationData.page - 1}
                rowsPerPage={groupsPaginationData.limit}
                onPageChange={(_, page) => onPageChange(page)}
                onRowsPerPageChange={onRowsPerPageChange}
              />
            </TableRow>
          </TableFooter>
        </Table>
      )}
    </>
  );
};
