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

import { EnhancedTableHead } from "@components/shared/enhancedTableHead";
import { HeadCell } from "@models/table";
import { ProjectType } from "@models/project";
import noProjectsUrl from "@assets/no_projects.png";
import { useMLStore } from "@store/ml.store";
import { MLModel, MLModelTypes } from "@models/ml";

export const DefaultMLModels: React.FC = () => {
  const { t } = useTranslation();
  const {
    defaultModels,
    defaultModelsPaginationData,
    defaultModelsFilterSortData,
    getModels,
    setPaginationData,
    setFilterSortData,
  } = useMLStore();

  const [search, setSearch] = useState("");
  const [debouncedSearch] = useDebounce(search, 500);

  useEffect(() => {
    getModels();
  }, []);

  useEffect(() => {
    if (debouncedSearch !== (defaultModelsFilterSortData.search || "")) {
      setFilterSortData(
        {
          ...defaultModelsFilterSortData,
          search: debouncedSearch === "" ? undefined : debouncedSearch,
        },
        MLModelTypes.Default
      );
    }
  }, [debouncedSearch]);

  const headCells: HeadCell[] = [
    {
      id: "name",
      label: t("ml.name"),
      enabledSort: true,
    },
    {
      id: "projectTypes",
      label: t("ml.projectTypes"),
    },
    {
      id: "objectTypes",
      label: t("ml.objectTypes"),
    },
  ];

  const handleRequestSort = (key: string) => {
    const isSameField = defaultModelsFilterSortData.sort === key;
    setFilterSortData(
      {
        ...defaultModelsFilterSortData,
        sort: key as keyof MLModel,
        reverse: isSameField ? !defaultModelsFilterSortData.reverse : false,
      },
      MLModelTypes.Default
    );
  };

  const onSearchChange = (e: ChangeEvent<HTMLInputElement>) => {
    setSearch(e.target.value);
  };

  const onTypeFilterChange = (e: SelectChangeEvent) => {
    setFilterSortData(
      {
        ...defaultModelsFilterSortData,
        filter: e.target.value as ProjectType,
      },
      MLModelTypes.Default
    );
  };

  const onPageChange = (page: number) => {
    setPaginationData(
      {
        ...defaultModelsPaginationData,
        page: page + 1,
      },
      MLModelTypes.Default
    );
  };

  const onRowsPerPageChange = (
    e: ChangeEvent<HTMLTextAreaElement | HTMLInputElement>
  ) => {
    const limit = +e.target.value;

    setPaginationData(
      {
        ...defaultModelsPaginationData,
        limit,
      },
      MLModelTypes.Default
    );
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
          id="ml-model-search"
        />
        <FormControl sx={{ width: 180 }} size="small">
          <InputLabel id="ml-model-type-filter-label">
            {t("general.type")}
          </InputLabel>
          <Select
            label={t("general.type")}
            labelId="ml-model-type-filter-label"
            value={defaultModelsFilterSortData.filter || ""}
            onChange={onTypeFilterChange}
            id="ml-model-type-filter"
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
      {!defaultModelsPaginationData.total ? (
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
          <Typography variant="h4">{t("ml.noMLModels")}</Typography>
        </Box>
      ) : (
        <Table sx={{ mt: 2 }} dir="ltr">
          <EnhancedTableHead
            headCells={headCells}
            order={defaultModelsFilterSortData.reverse ? "asc" : "desc"}
            orderBy={defaultModelsFilterSortData.sort || ""}
            onRequestSort={handleRequestSort}
          />
          <TableBody>
            {defaultModels.map((model) => (
              <TableRow
                key={model.id}
                sx={{ "&:last-child td, &:last-child th": { border: 0 } }}
              >
                <TableCell sx={{ maxWidth: 500 }}>
                  <Typography
                    variant="body1"
                    sx={{
                      fontWeight: "bold",
                      wordWrap: "break-word",
                    }}
                  >
                    {model.name}
                  </Typography>
                </TableCell>
                <TableCell>
                  {model.type_of_data
                    .map((type) => t(`types.${type}`))
                    .join(", ")}
                </TableCell>
                <TableCell>{model.type_of_objects.join(", ")}</TableCell>
              </TableRow>
            ))}
          </TableBody>
          <TableFooter>
            <TableRow>
              <TablePagination
                count={defaultModelsPaginationData.total}
                page={defaultModelsPaginationData.page - 1}
                rowsPerPage={defaultModelsPaginationData.limit}
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
