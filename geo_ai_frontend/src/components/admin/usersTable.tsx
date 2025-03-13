import React, { useState, ChangeEvent, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { useDebounce } from "use-debounce";
import {
  Box,
  FormControl,
  IconButton,
  InputAdornment,
  InputLabel,
  MenuItem,
  Select,
  SelectChangeEvent,
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
import CircleIcon from "@mui/icons-material/Circle";
import EditIcon from "@mui/icons-material/Edit";
import SendIcon from "@mui/icons-material/Send";

import { Role, User } from "@models/user";
import { useAdminStore } from "@store/admin.store";
import { EnhancedTableHead } from "@components/shared/enhancedTableHead";
import { HeadCell } from "@models/table";
import { UserModal } from "./userModal";

export const UsersTable: React.FC = () => {
  const { t } = useTranslation();
  const {
    users,
    paginationData,
    filterSortData,
    getUsers,
    updateUserStatus,
    resendInvite,
    setPaginationData,
    setFilterSortData,
  } = useAdminStore();

  const [search, setSearch] = useState("");
  const [debouncedSearch] = useDebounce(search, 500);

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedUser, setSelectedUser] = useState<User>();

  useEffect(() => {
    getUsers({
      page: paginationData.page,
      limit: paginationData.limit,
      ...filterSortData,
    });
  }, []);

  useEffect(() => {
    if (debouncedSearch !== (filterSortData.search || "")) {
      setFilterSortData({
        ...filterSortData,
        search: debouncedSearch === "" ? undefined : debouncedSearch,
      });
    }
  }, [debouncedSearch]);

  const headCells: HeadCell[] = [
    {
      id: "id",
      label: t("admin.id"),
      enabledSort: true,
    },
    {
      id: "username",
      label: t("admin.username"),
    },
    {
      id: "role",
      label: t("general.role"),
      enabledSort: true,
    },
    {
      id: "type",
      label: t("general.type"),
    },
    {
      id: "status",
      label: t("admin.status"),
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
    const isSameField = filterSortData.sort === key;
    setFilterSortData({
      ...filterSortData,
      sort: key as keyof User,
      reverse: isSameField ? !filterSortData.reverse : false,
    });
  };

  const onSearchChange = (e: ChangeEvent<HTMLInputElement>) => {
    setSearch(e.target.value);
  };

  const onRoleFilterChange = (e: SelectChangeEvent) => {
    setFilterSortData({
      ...filterSortData,
      filter: e.target.value as Role,
    });
  };

  const onPageChange = (page: number) => {
    setPaginationData({
      ...paginationData,
      page: page + 1,
    });
  };

  const onRowsPerPageChange = (
    e: ChangeEvent<HTMLTextAreaElement | HTMLInputElement>
  ) => {
    const limit = +e.target.value;

    setPaginationData({
      ...paginationData,
      limit,
    });
  };

  const onStatusChange = (
    e: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>,
    user: User
  ) => {
    updateUserStatus({
      id: user.id,
      status: e.target.value === "true",
    });
  };

  const onEditUser = (user: User) => {
    setSelectedUser(user);
    setIsModalOpen(true);
  };

  const onSendInvitation = (user: User) => {
    resendInvite(user.id);
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
        <FormControl sx={{ width: 180 }} size="small">
          <InputLabel id="user-role-filter-label">
            {t("general.role")}
          </InputLabel>
          <Select
            label={t("general.role")}
            labelId="user-role-filter-label"
            value={filterSortData.filter || ""}
            onChange={onRoleFilterChange}
            id="user-role-filter"
          >
            <MenuItem value="all">{t(`roles.all`)}</MenuItem>
            {Object.values(Role).map((r) => (
              <MenuItem key={r} value={r}>
                {t(`roles.${r}`)}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
      </Box>
      <Table sx={{ mt: 2 }} dir="ltr">
        <EnhancedTableHead
          headCells={headCells}
          order={filterSortData.reverse ? "asc" : "desc"}
          orderBy={filterSortData.sort || ""}
          onRequestSort={handleRequestSort}
        />
        <TableBody>
          {users.map((user) => (
            <TableRow
              key={user.id}
              sx={{ "&:last-child td, &:last-child th": { border: 0 } }}
            >
              <TableCell>{user.id}</TableCell>
              <TableCell sx={{ maxWidth: 300 }}>
                <Typography
                  variant="body1"
                  sx={{ fontWeight: "bold", wordWrap: "break-word" }}
                >
                  {user.username}
                </Typography>
                <Typography variant="body1">{user.email}</Typography>
              </TableCell>
              <TableCell>{t(`roles.${user.role}`)}</TableCell>
              <TableCell>
                {user.external_user ? t("admin.external") : t("admin.internal")}
              </TableCell>
              <TableCell>
                <TextField
                  select
                  size="small"
                  value={user.is_active}
                  onChange={(e) => onStatusChange(e, user)}
                  sx={{
                    width: 140,
                    ".MuiInputBase-root": { borderRadius: "100px" },
                  }}
                  id={`user-${user.id}-status-select`}
                >
                  <MenuItem value="true">
                    <CircleIcon color="success" sx={{ fontSize: 12, mr: 1 }} />
                    {t(`admin.active`)}
                  </MenuItem>
                  <MenuItem value="false">
                    <CircleIcon color="warning" sx={{ fontSize: 12, mr: 1 }} />
                    {t(`admin.inactive`)}
                  </MenuItem>
                </TextField>
              </TableCell>
              <TableCell>
                {t("intlDateTime", {
                  val: new Date(user.created_at),
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
                    onClick={() => onEditUser(user)}
                    id={`user-${user.id}-edit-button`}
                    disabled={!user.is_active}
                  >
                    <EditIcon />
                  </IconButton>
                  <IconButton
                    onClick={() => onSendInvitation(user)}
                    id={`user-${user.id}-send-invitation-button`}
                    disabled={!user.is_active}
                  >
                    <SendIcon />
                  </IconButton>
                </Box>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
        <TableFooter>
          <TableRow>
            <TablePagination
              count={paginationData.total}
              page={paginationData.page - 1}
              rowsPerPage={paginationData.limit}
              onPageChange={(_, page) => onPageChange(page)}
              onRowsPerPageChange={onRowsPerPageChange}
            />
          </TableRow>
        </TableFooter>
      </Table>
      <UserModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        user={selectedUser}
      />
    </>
  );
};
