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
  Button,
  Tooltip,
} from "@mui/material";
import SearchIcon from "@mui/icons-material/Search";
import CircleIcon from "@mui/icons-material/Circle";
import RefreshIcon from "@mui/icons-material/Refresh";
import InfoOutlinedIcon from "@mui/icons-material/InfoOutlined";

import { EnhancedTableHead } from "@components/shared/enhancedTableHead";
import { HeadCell } from "@models/table";
import { ProjectType } from "@models/project";
import noProjectsUrl from "@assets/no_projects.png";
import { useMLStore } from "@store/ml.store";
import { MLModel, MLModelTypes, MLStatus } from "@models/ml";
import { CreatedMLModelActionButtons } from "./tableActionButtons";

export const CreatedMLModels: React.FC = () => {
  const { t } = useTranslation();
  const {
    createdModels,
    createdModelsPaginationData,
    createdModelsFilterSortData,
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
    if (debouncedSearch !== (createdModelsFilterSortData.search || "")) {
      setFilterSortData(
        {
          ...createdModelsFilterSortData,
          search: debouncedSearch === "" ? undefined : debouncedSearch,
        },
        MLModelTypes.Created
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
      id: "objectTypes",
      label: t("ml.objectTypes"),
    },
    {
      id: "status",
      label: t("ml.status"),
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
      label: t("ml.action"),
    },
  ];

  const handleRequestSort = (key: string) => {
    const isSameField = createdModelsFilterSortData.sort === key;
    setFilterSortData(
      {
        ...createdModelsFilterSortData,
        sort: key as keyof MLModel,
        reverse: isSameField ? !createdModelsFilterSortData.reverse : false,
      },
      MLModelTypes.Created
    );
  };

  const onSearchChange = (e: ChangeEvent<HTMLInputElement>) => {
    setSearch(e.target.value);
  };

  const onTypeFilterChange = (e: SelectChangeEvent) => {
    setFilterSortData(
      {
        ...createdModelsFilterSortData,
        filter: e.target.value as ProjectType,
      },
      MLModelTypes.Created
    );
  };

  const onPageChange = (page: number) => {
    setPaginationData(
      {
        ...createdModelsPaginationData,
        page: page + 1,
      },
      MLModelTypes.Created
    );
  };

  const onRowsPerPageChange = (
    e: ChangeEvent<HTMLTextAreaElement | HTMLInputElement>
  ) => {
    const limit = +e.target.value;

    setPaginationData(
      {
        ...createdModelsPaginationData,
        limit,
      },
      MLModelTypes.Created
    );
  };

  const getStatusColor = (model: MLModel) => {
    switch (model.status) {
      case MLStatus.NotTrained:
        return "info";
      case MLStatus.InTraining:
      case MLStatus.Loading:
        return "warning";
      case MLStatus.Trained:
      case MLStatus.Ready:
        return "success";
      case MLStatus.Error:
        return "error";
    }
  };

  const onRefresh = () => {
    getModels();
  };

  return (
    <>
      <Box
        component="div"
        sx={{ display: "flex", mt: 2, gap: 2, justifyContent: "space-between" }}
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
            id="ml-model-search"
          />
          <FormControl sx={{ width: 180 }} size="small">
            <InputLabel id="ml-model-type-filter-label">
              {t("general.type")}
            </InputLabel>
            <Select
              label={t("general.type")}
              labelId="ml-model-type-filter-label"
              value={createdModelsFilterSortData.filter}
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
        <Button variant="text" endIcon={<RefreshIcon />} onClick={onRefresh}>
          {t("general.refresh")}
        </Button>
      </Box>
      {!createdModelsPaginationData.total ? (
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
            order={createdModelsFilterSortData.reverse ? "asc" : "desc"}
            orderBy={createdModelsFilterSortData.sort || ""}
            onRequestSort={handleRequestSort}
          />
          <TableBody>
            {createdModels.map((model) => (
              <TableRow
                key={model.id}
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
                    {model.name}
                  </Typography>
                  {model.type_of_data
                    .map((type) => t(`types.${type}`))
                    .join(", ")}
                </TableCell>
                <TableCell sx={{ maxWidth: 300 }}>
                  {model.type_of_objects.join(", ")}
                </TableCell>
                <TableCell>
                  <Box
                    component="div"
                    sx={{ display: "flex", alignItems: "center" }}
                  >
                    <CircleIcon
                      color={getStatusColor(model)}
                      sx={{ fontSize: 12, mr: 1 }}
                    />
                    {t(
                      `mlStatuses.${
                        Object.keys(MLStatus)[
                          Object.values(MLStatus).indexOf(model.status)
                        ]
                      }`
                    )}
                    {model.status === MLStatus.Error &&
                      model.translatedInfo && (
                        <Tooltip title={model.translatedInfo}>
                          <InfoOutlinedIcon sx={{ fontSize: 18, ml: 1 }} />
                        </Tooltip>
                      )}
                  </Box>
                </TableCell>
                <TableCell>
                  {t("intlDateTime", {
                    val: new Date(model.created_at),
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
                <TableCell sx={{ maxWidth: 300 }}>{model.created_by}</TableCell>
                <TableCell>
                  <CreatedMLModelActionButtons model={model} />
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
          <TableFooter>
            <TableRow>
              <TablePagination
                count={createdModelsPaginationData.total}
                page={createdModelsPaginationData.page - 1}
                rowsPerPage={createdModelsPaginationData.limit}
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
