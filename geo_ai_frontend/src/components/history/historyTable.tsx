import React, { useState, ChangeEvent, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { useDebounce } from "use-debounce";
import { useNavigate } from "react-router-dom";
import { DatePicker, LocalizationProvider } from "@mui/x-date-pickers";
import { AdapterDayjs } from "@mui/x-date-pickers/AdapterDayjs";
import {
  Box,
  Button,
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
  Modal,
} from "@mui/material";
import { Dayjs } from "dayjs";
import SearchIcon from "@mui/icons-material/Search";
import CloseIcon from "@mui/icons-material/Close";

import { ModalContent } from "@components/shared/modalContent";
import { EnhancedTableHead } from "@components/shared/enhancedTableHead";
import { HeadCell } from "@models/table";
import noProjectsUrl from "@assets/no_projects.png";
import { useHistoryStore } from "@store/history.store";
import { History, HistoryType, ObjectHistory } from "@models/history";
import { ERRORS } from "@models/error";

export const HistoryTable: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const {
    history,
    historyType,
    paginationData,
    filterSortData,
    setPaginationData,
    setFilterSortData,
    getHistory,
  } = useHistoryStore();

  const [search, setSearch] = useState("");
  const [debouncedSearch] = useDebounce(search, 500);
  const [descriptionToView, setDescriptionToView] = useState<string>();

  useEffect(() => {
    getHistory();
  }, []);

  useEffect(() => {
    if (debouncedSearch !== (filterSortData.search || "")) {
      setFilterSortData({
        ...filterSortData,
        search: debouncedSearch === "" ? undefined : debouncedSearch,
      });
    }
  }, [debouncedSearch]);

  const generalHeadCells: HeadCell[] = [
    {
      id: "date",
      label: t("history.date"),
      enabledSort: true,
    },
    {
      id: "user_action",
      label: t("history.action"),
    },
    {
      id: "username",
      label: t("history.username"),
    },
    {
      id: "project",
      label: t("history.project"),
    },
    {
      id: "description",
      label: t("history.description"),
    },
  ];

  const objectHeadCells: HeadCell[] = [
    {
      id: "date",
      label: t("history.date"),
      enabledSort: true,
    },
    {
      id: "object_name",
      label: t("history.object"),
      enabledSort: true,
    },
    {
      id: "action",
      label: t("history.action"),
    },
    {
      id: "username",
      label: t("history.username"),
    },
    {
      id: "project",
      label: t("history.project"),
    },
    {
      id: "description",
      label: t("history.description"),
    },
  ];

  const handleRequestSort = (key: string) => {
    const isSameField = filterSortData.sort === key;
    setFilterSortData({
      ...filterSortData,
      sort: key as keyof (History | ObjectHistory),
      reverse: isSameField ? !filterSortData.reverse : false,
    });
  };

  const onSearchChange = (e: ChangeEvent<HTMLInputElement>) => {
    setSearch(e.target.value);
  };

  const onFromDateFilterChange = (value: Dayjs | null) => {
    setFilterSortData({
      ...filterSortData,
      from_date: value,
    });
  };

  const onToDateFilterChange = (value: Dayjs | null) => {
    setFilterSortData({
      ...filterSortData,
      to_date: value,
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

  const onViewDescription = (desc: string, code?: keyof typeof ERRORS) => {
    const text = code && ERRORS[code] ? t(ERRORS[code]) : desc;

    setDescriptionToView(text || t(ERRORS.OTHER));
  };

  const onProjectNameClick = (
    id: string | undefined,
    isComparison: boolean
  ) => {
    if (!id) {
      navigate("/404");
    }
    navigate(`/projects${isComparison ? "/comparison" : ""}/${id}`);
  };

  const onModalClose = () => {
    setDescriptionToView(undefined);
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
        <LocalizationProvider dateAdapter={AdapterDayjs}>
          <DatePicker
            label={t("history.fromFilter")}
            value={filterSortData.from_date || null}
            onChange={onFromDateFilterChange}
            maxDate={filterSortData.to_date ?? undefined}
            slotProps={{
              textField: { size: "small", id: "from-date-filter-select" },
            }}
            sx={{ maxWidth: 150 }}
          />
          <DatePicker
            label={t("history.toFilter")}
            value={filterSortData.to_date || null}
            onChange={onToDateFilterChange}
            minDate={filterSortData.from_date ?? undefined}
            slotProps={{
              textField: { size: "small", id: "to-date-filter-select" },
            }}
            sx={{ maxWidth: 150 }}
          />
        </LocalizationProvider>
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
          <Typography variant="h4">{t("history.noHistory")}</Typography>
        </Box>
      ) : (
        <Table sx={{ mt: 2 }} dir="ltr">
          <EnhancedTableHead
            headCells={
              historyType === HistoryType.Object
                ? objectHeadCells
                : generalHeadCells
            }
            order={filterSortData.reverse ? "asc" : "desc"}
            orderBy={filterSortData.sort || ""}
            onRequestSort={handleRequestSort}
          />
          <TableBody>
            {history.map((entity) => (
              <TableRow
                key={entity.id}
                sx={{ "&:last-child td, &:last-child th": { border: 0 } }}
              >
                <TableCell>
                  {t("intlDateTime", {
                    val: new Date(entity.date),
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
                <TableCell sx={{ maxWidth: 600 }}>
                  <Typography
                    variant="body1"
                    sx={{
                      fontWeight: "bold",
                      overflow: "hidden",
                      textOverflow: "ellipsis",
                    }}
                  >
                    {(entity as History).user_action ||
                      (entity as ObjectHistory).action}
                  </Typography>
                </TableCell>
                {historyType === HistoryType.Object && (
                  <TableCell sx={{ maxWidth: 600 }}>
                    <Typography
                      variant="body1"
                      sx={{
                        fontWeight: "bold",
                        overflow: "hidden",
                        textOverflow: "ellipsis",
                      }}
                    >
                      {(entity as ObjectHistory).object_name}
                    </Typography>
                  </TableCell>
                )}
                <TableCell sx={{ maxWidth: 300 }}>
                  <Typography variant="body1" sx={{ wordWrap: "break-word" }}>
                    {entity.username}
                  </Typography>
                </TableCell>
                <TableCell sx={{ maxWidth: 300 }}>
                  {entity.project_id && (entity as History).project_type ? (
                    <Button
                      sx={{
                        textTransform: "none",
                        textAlign: "left",
                        wordBreak: "break-all",
                        ml: -1,
                      }}
                      id={`ml-${entity.id}-project-link`}
                      onClick={() =>
                        onProjectNameClick(
                          entity.project_id,
                          (entity as History).project_type === "PROJECT_COMPARE"
                        )
                      }
                    >
                      {entity.project}
                    </Button>
                  ) : (
                    <Typography variant="body2" sx={{ wordWrap: "break-word" }}>
                      {entity.project}
                    </Typography>
                  )}
                </TableCell>
                <TableCell>
                  {entity.description && (
                    <Button
                      sx={{ textTransform: "none", ml: -1 }}
                      id={`ml-${entity.id}-create-button`}
                      onClick={() =>
                        onViewDescription(
                          entity.description,
                          (entity as History).code
                        )
                      }
                    >
                      {t("history.view")}
                    </Button>
                  )}
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
      <Modal open={!!descriptionToView} onClose={onModalClose}>
        <ModalContent>
          <IconButton
            sx={{ position: "absolute", alignSelf: "end" }}
            onClick={onModalClose}
            id="close-modal-button"
          >
            <CloseIcon />
          </IconButton>
          <Typography
            variant="h6"
            sx={{ alignSelf: "start", mb: 2, fontWeight: "bold" }}
          >
            {t("history.description")}
          </Typography>
          <Typography variant="body1" sx={{ alignSelf: "start" }}>
            {descriptionToView}
          </Typography>
        </ModalContent>
      </Modal>
    </>
  );
};
