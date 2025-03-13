import React, { useState, ChangeEvent, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { useDebounce } from "use-debounce";
import {
  Box,
  Button,
  FormControl,
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
import RefreshIcon from "@mui/icons-material/Refresh";

import noProjectsUrl from "@assets/no_projects.png";

import { EnhancedTableHead } from "@components/shared/enhancedTableHead";
import { StatusLabel } from "@components/shared/statusLabel";
import { ProjectActionButtons } from "@components/project/tableActionButtons";
import { useProjectListStore } from "@store/projectList.store";
import { HeadCell } from "@models/table";
import { Project, ProjectType } from "@models/project";

export const ProjectsTable: React.FC = () => {
  const { t } = useTranslation();
  const {
    projects,
    paginationData,
    filterSortData,
    getProjects,
    setPaginationData,
    setFilterSortData,
  } = useProjectListStore();

  const [search, setSearch] = useState("");
  const [debouncedSearch] = useDebounce(search, 500);

  useEffect(() => {
    getProjects();
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
      id: "name",
      label: t("project.name"),
      enabledSort: true,
    },
    {
      id: "date",
      label: t("project.dateShooted"),
      enabledSort: true,
    },
    {
      id: "type",
      label: t("project.type"),
    },
    {
      id: "status",
      label: t("project.status"),
    },
    {
      id: "created_at",
      label: t("general.dateCreated"),
      enabledSort: true,
    },
    {
      id: "created_by",
      label: t("general.createdBy"),
      enabledSort: true,
    },
    {
      id: "action",
      label: t("project.action"),
    },
  ];

  const handleRequestSort = (key: string) => {
    const isSameField = filterSortData.sort === key;
    setFilterSortData({
      ...filterSortData,
      sort: key as keyof Project,
      reverse: isSameField ? !filterSortData.reverse : false,
    });
  };

  const onSearchChange = (e: ChangeEvent<HTMLInputElement>) => {
    setSearch(e.target.value);
  };

  const onTypeFilterChange = (e: SelectChangeEvent) => {
    setFilterSortData({
      ...filterSortData,
      filter: e.target.value as ProjectType,
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

  const onRefresh = () => {
    getProjects();
  };

  return (
    <>
      <Box
        component="div"
        sx={{ display: "flex", mt: 2, justifyContent: "space-between" }}
        dir="ltr"
      >
        <Box component="div" sx={{ display: "flex", gap: 2 }} dir="ltr">
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
            id="project-search"
          />
          <FormControl sx={{ width: 180 }} size="small">
            <InputLabel id="project-type-filter-label">
              {t("general.type")}
            </InputLabel>
            <Select
              label={t("general.type")}
              labelId="project-type-filter-label"
              value={filterSortData.filter}
              onChange={onTypeFilterChange}
              id="project-type-filter"
            >
              <MenuItem value="all">{t(`types.all`)}</MenuItem>
              {Object.values(ProjectType).map((type) => (
                <MenuItem key={type} value={type}>
                  {t(`types.${type}`)}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Box>
        <Button variant="text" endIcon={<RefreshIcon />} onClick={onRefresh}>
          {t("general.refresh")}
        </Button>
      </Box>
      {!paginationData.total ? (
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
          <Typography variant="h4">{t("project.noProjects")}</Typography>
        </Box>
      ) : (
        <Table sx={{ mt: 2 }} dir="ltr">
          <EnhancedTableHead
            headCells={headCells}
            order={filterSortData.reverse ? "asc" : "desc"}
            orderBy={filterSortData.sort || ""}
            onRequestSort={handleRequestSort}
          />
          <TableBody>
            {projects.map((project) => (
              <TableRow
                key={project.id}
                sx={{ "&:last-child td, &:last-child th": { border: 0 } }}
              >
                <TableCell sx={{ maxWidth: 400 }}>
                  <Typography
                    variant="body1"
                    sx={{
                      fontWeight: "bold",
                      wordWrap: "break-word",
                    }}
                  >
                    {project.name}
                  </Typography>
                </TableCell>
                <TableCell>
                  {t("intlDateTime", {
                    val: new Date(project.date),
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
                <TableCell>{t(`types.${project.type}`)}</TableCell>
                <TableCell>
                  <StatusLabel
                    status={project.status}
                    translatedInfo={project.translatedInfo}
                  />
                </TableCell>
                <TableCell>
                  {t("intlDateTime", {
                    val: new Date(project.created_at),
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
                <TableCell sx={{ maxWidth: 400 }}>
                  {project.created_by}
                </TableCell>
                <TableCell>
                  <ProjectActionButtons project={project} />
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
                labelRowsPerPage={t("general.rowsPerPage")}
              />
            </TableRow>
          </TableFooter>
        </Table>
      )}
    </>
  );
};
