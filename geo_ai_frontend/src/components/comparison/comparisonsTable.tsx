import React, { useState, ChangeEvent, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { useDebounce } from "use-debounce";
import {
  Box,
  InputAdornment,
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
  FormControl,
  InputLabel,
} from "@mui/material";
import SearchIcon from "@mui/icons-material/Search";

import noProjectsUrl from "@assets/no_projects.png";

import { EnhancedTableHead } from "@components/shared/enhancedTableHead";
import { StatusLabel } from "@components/shared/statusLabel";
import { ComparisonActionButtons } from "@components/comparison/tableActionButtons";
import { useComparisonStore } from "@store/comparison.store";
import { HeadCell } from "@models/table";
import { ProjectType } from "@models/project";
import { Comparison } from "@models/comparison";

export const ComparisonsTable: React.FC = () => {
  const { t } = useTranslation();
  const {
    comparisons,
    paginationData,
    filterSortData,
    setPaginationData,
    setFilterSortData,
    getComparisons,
  } = useComparisonStore();

  const [search, setSearch] = useState("");
  const [debouncedSearch] = useDebounce(search, 500);

  useEffect(() => {
    getComparisons();
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
      id: "project_1",
      label: t("comparison.project1"),
      enabledSort: true,
    },
    {
      id: "project_2",
      label: t("comparison.project2"),
      enabledSort: true,
    },
    {
      id: "status",
      label: t("comparison.status"),
    },
    {
      id: "created_at",
      label: t("general.dateCreated"),
      enabledSort: true,
    },
    {
      id: "action",
      label: t("comparison.action"),
    },
  ];

  const handleRequestSort = (key: string) => {
    const isSameField = filterSortData.sort === key;
    setFilterSortData({
      ...filterSortData,
      sort: key as keyof Comparison,
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
          id="comparion-search"
        />
        <FormControl sx={{ width: 180 }} size="small">
          <InputLabel id="project-type-filter-label">
            {t("general.type")}
          </InputLabel>
          <Select
            label={t("general.type")}
            labelId="project-type-filter-label"
            value={filterSortData.filter || ""}
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
          <Typography variant="h4">{t("comparison.noComparisons")}</Typography>
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
            {comparisons.map((comparison) => (
              <TableRow
                key={comparison.id}
                sx={{ "&:last-child td, &:last-child th": { border: 0 } }}
              >
                <TableCell sx={{ maxWidth: 300 }}>
                  <Typography
                    variant="body1"
                    sx={{
                      fontWeight: "bold",
                      wordWrap: "break-word",
                    }}
                  >
                    {comparison.project_1.name}
                  </Typography>
                  <Typography variant="body1">
                    {t(`types.${comparison.type}`)}
                  </Typography>
                </TableCell>
                <TableCell sx={{ maxWidth: 300 }}>
                  <Typography
                    variant="body1"
                    sx={{
                      fontWeight: "bold",
                      wordWrap: "break-word",
                    }}
                  >
                    {comparison.project_2.name}
                  </Typography>
                  <Typography variant="body1">
                    {t(`types.${comparison.type}`)}
                  </Typography>
                </TableCell>
                <TableCell>
                  <StatusLabel
                    status={comparison.status}
                    translatedInfo={comparison.translatedInfo}
                  />
                </TableCell>
                <TableCell>
                  {t("intlDateTime", {
                    val: new Date(comparison.created_at),
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
                  <ComparisonActionButtons comparison={comparison} />
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
      )}
    </>
  );
};
