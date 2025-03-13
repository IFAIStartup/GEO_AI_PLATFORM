import React, { useState, useRef, MouseEvent, ChangeEvent } from "react";
import {
  setIntervalAsync,
  clearIntervalAsync,
  SetIntervalAsyncTimer,
} from "set-interval-async/fixed";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";
import dayjs from "dayjs";
import {
  Alert,
  Autocomplete,
  Box,
  Button,
  CircularProgress,
  IconButton,
  Menu,
  MenuItem,
  Modal,
  TextField,
  Typography,
  createFilterOptions,
} from "@mui/material";
import { AdapterDayjs } from "@mui/x-date-pickers/AdapterDayjs";
import { DateTimePicker, LocalizationProvider } from "@mui/x-date-pickers";
import CloseIcon from "@mui/icons-material/Close";
import ArrowDropDownIcon from "@mui/icons-material/ArrowDropDown";
import ArrowDropUpIcon from "@mui/icons-material/ArrowDropUp";

import { ModalContent } from "@components/shared/modalContent";
import { ProjectType } from "@models/project";
import { ApiError, TaskStatus } from "@models/common";
import { useProjectListStore } from "@store/projectList.store";
import { useAlertStore } from "@store/alert.store";
import { getTaskStatus } from "@services/project";
import { ERRORS } from "@models/error";

const filter = createFilterOptions<string>();

export const CreateProjectMenu: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const createProject = useProjectListStore((state) => state.createProject);
  const getProjects = useProjectListStore((state) => state.getProjects);
  const getFolders = useProjectListStore((state) => state.getFolders);
  const folders = useProjectListStore((state) => state.folders);
  const { setAlert } = useAlertStore();

  const interval = useRef<SetIntervalAsyncTimer<[]>>();
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const isMenuOpen = Boolean(anchorEl);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isProjectCreating, setIsProjectCreating] = useState(false);
  const [selectedType, setSelectedType] = useState<ProjectType>(
    ProjectType.Aerial
  );

  const [name, setName] = useState("");
  const [nameError, setNameError] = useState("");
  const [date, setDate] = useState(dayjs());
  const [folderName, setFolderName] = useState("");
  const [folderNameError, setFolderNameError] = useState("");
  const [error, setError] = useState("");

  const onMenuOpen = (event: MouseEvent<HTMLButtonElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const onMenuClose = () => {
    setAnchorEl(null);
  };

  const onModalOpen = (type: ProjectType) => {
    setSelectedType(type);
    setDate(dayjs());
    setIsModalOpen(true);
    getFolders(type);
    onMenuClose();
  };

  const onModalClose = () => {
    setIsModalOpen(false);
    setIsProjectCreating(false);
    setSelectedType(ProjectType.Aerial);
    setName("");
    setFolderName("");
    setNameError("");
    setFolderNameError("");
    setError("");
    if (interval.current) {
      clearIntervalAsync(interval.current);
    }
    getProjects();
  };

  const onNameChange = (
    e: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
    setName(e.target.value);
    setNameError("");
  };

  const onFolderNameChange = (value: string) => {
    setFolderName(value);
    setFolderNameError("");
  };

  const onSubmit = () => {
    if (!name) {
      setNameError(t("project.nameError"));
    }
    if (!folderName) {
      setFolderNameError(t("project.folderNameError"));
    }
    if (!name || !folderName) {
      return;
    }

    setError("");
    setIsProjectCreating(true);

    createProject({
      name,
      date: date.toDate(),
      link: folderName,
      type: selectedType,
    })
      .then((response) => {
        interval.current = setIntervalAsync(async () => {
          const { data } = await getTaskStatus(response.task_id);
          if (data.task_status === TaskStatus.Success) {
            onModalClose();
            navigate(`/projects/${response.project.id}`);
            return;
          } else if (data.task_status === TaskStatus.Failure) {
            setAlert({
              severity: "error",
              key: "general.error",
            });
            if (interval.current) {
              clearIntervalAsync(interval.current);
            }
            onModalClose();
          }
        }, 5000);
      })
      .catch((e: ApiError) => {
        const err = e.response?.data.detail;
        setIsProjectCreating(false);

        const nameErrors: Array<keyof typeof ERRORS> = [
          "PROJECT_NAME_TOO_SHORT",
          "PROJECT_EXIST",
        ];
        const folderErrors: Array<keyof typeof ERRORS> = [
          "FOLDER_IS_EMPTY",
          "FOLDER_NOT_EXIST",
          "FOLDER_EMPTY_OR_NOT_EXIST",
          "TIF_OR_JPG_FILES_NOT_FOUND",
          "MORE_OR_LESS_THAN_ONE_LAS_FILE",
          "MORE_OR_LESS_THAN_ONE_CSV_FILE",
          "NO_JPG_FILES",
          "INVALID_FOLDER_FORMAT",
        ];

        if (err?.code && nameErrors.includes(err.code)) {
          setNameError(t(ERRORS[err.code]));
        } else if (err?.code && folderErrors.includes(err.code)) {
          setFolderNameError(t(ERRORS[err.code]));
        } else {
          setError(err?.message || t(ERRORS.OTHER));
        }
      });
  };

  return (
    <>
      <Button
        variant="contained"
        onClick={onMenuOpen}
        endIcon={isMenuOpen ? <ArrowDropUpIcon /> : <ArrowDropDownIcon />}
        id="create-project-menu"
      >
        {t("project.createProject")}
      </Button>
      <Menu anchorEl={anchorEl} open={isMenuOpen} onClose={onMenuClose}>
        {Object.values(ProjectType).map((type) => (
          <MenuItem key={type} value={type} onClick={() => onModalOpen(type)}>
            {t(`types.${type}`)}
          </MenuItem>
        ))}
      </Menu>
      <Modal open={isModalOpen} onClose={onModalClose}>
        <ModalContent>
          <IconButton
            sx={{ alignSelf: "end" }}
            onClick={onModalClose}
            id="close-modal-button"
          >
            <CloseIcon />
          </IconButton>
          <Typography variant="h5">
            {t("project.uploadingHeader", { type: t(`types.${selectedType}`) })}
          </Typography>
          <Typography variant="body1" sx={{ textAlign: "center", px: 10 }}>
            {t("project.uploadingSubHeader")}
          </Typography>
          <Box
            component="div"
            sx={{
              display: "flex",
              flexDirection: "column",
              width: 400,
              gap: 4,
              mt: 3,
            }}
          >
            <TextField
              required
              fullWidth
              id="name"
              label={t("project.name")}
              value={name}
              onChange={onNameChange}
              error={!!nameError}
              helperText={nameError}
            />
            <LocalizationProvider dateAdapter={AdapterDayjs}>
              <DateTimePicker
                label={t("project.dateShooted")}
                value={date}
                onChange={(v) => v && setDate(v)}
              />
            </LocalizationProvider>
            <Autocomplete
              id="folder-select"
              freeSolo
              value={folderName}
              onChange={(_, v) => onFolderNameChange(v ?? "")}
              options={folders}
              selectOnFocus
              clearOnBlur
              filterOptions={(options, params) => {
                const filtered = filter(options, params);

                const { inputValue } = params;
                // Suggest the creation of a new value
                const isExisting = options.some(
                  (option) => inputValue === option
                );
                if (inputValue !== "" && !isExisting) {
                  filtered.push(inputValue);
                }

                return filtered;
              }}
              renderInput={(params) => (
                <TextField
                  {...params}
                  label={t("project.folderName")}
                  required
                  error={!!folderNameError}
                  helperText={folderNameError}
                />
              )}
            />
            {!!error && <Alert severity="error">{error}</Alert>}
          </Box>
          <Box
            component="div"
            sx={{
              display: "flex",
              flexDirection: "column",
              width: 400,
              gap: 2,
              mt: 4,
            }}
          >
            <Button
              variant="contained"
              onClick={onSubmit}
              disabled={
                !date.isValid() ||
                !!nameError ||
                !!folderNameError ||
                isProjectCreating
              }
              fullWidth
              id="create-project-button"
            >
              {isProjectCreating ? (
                <CircularProgress color="inherit" size={24} />
              ) : (
                t("general.create")
              )}
            </Button>
            <Button
              variant="text"
              onClick={onModalClose}
              fullWidth
              id="cancel-modal-button"
            >
              {t("general.cancel")}
            </Button>
          </Box>
        </ModalContent>
      </Modal>
    </>
  );
};
