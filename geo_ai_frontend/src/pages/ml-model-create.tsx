import React, { useState, ChangeEvent, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";
import {
  Box,
  Button,
  Typography,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  SelectChangeEvent,
  createFilterOptions,
  Autocomplete,
  Alert,
  FormHelperText,
} from "@mui/material";

import { useMLStore } from "@store/ml.store";
import { ProjectType } from "@models/project";
import { ApiError } from "@models/common";
import { ERRORS } from "@models/error";
import { AdditionalMLDataType } from "@models/ml";

const filter = createFilterOptions<string>();

export const CreateMLModelPage: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const createModel = useMLStore((state) => state.createModel);
  const getFolders = useMLStore((state) => state.getFolders);
  const folders = useMLStore((state) => state.folders);

  const [name, setName] = useState("");
  const [nameError, setNameError] = useState("");
  const [folderName, setFolderName] = useState("");
  const [folderNameError, setFolderNameError] = useState("");
  const [type, setType] = useState<ProjectType | "">("");
  const [typeError, setTypeError] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    getFolders();
  }, []);

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

  const onTypeChange = (e: SelectChangeEvent<typeof type>) => {
    const {
      target: { value },
    } = e;
    setType(value ? (value as ProjectType) : "");
    setTypeError("");
  };

  const onCancel = () => {
    navigate("/ml");
  };

  const onCreate = () => {
    if (!name) {
      setNameError(t("ml.nameError1"));
    }
    if (!folderName) {
      setFolderNameError(t("ml.folderError"));
    }
    if (!type) {
      setTypeError(t("ml.typeError"));
    }
    if (!name || !folderName || !type) {
      return;
    }

    setError("");

    createModel({
      name,
      link: folderName,
      type_of_data: type,
    })
      .then((modelId) => {
        navigate(`/ml/${modelId}`);
      })
      .catch((e: ApiError) => {
        const err = e.response?.data.detail;

        if (err?.code === "ML_MODEL_NAME_ALREADY_EXIST") {
          setNameError(t(ERRORS[err.code]));
        } else {
          setError(err?.message || t(ERRORS.OTHER));
        }
      });
  };

  return (
    <Box
      component="div"
      sx={{
        display: "flex",
        flexDirection: "column",
        height: "calc(100vh - 112px)",
        alignItems: "center",
      }}
    >
      <Box
        component="div"
        sx={{
          flexGrow: 1,
          minWidth: 500,
        }}
      >
        <Typography variant="h5">{t("ml.createStepTitle")}</Typography>
        <Typography variant="body1" sx={{ opacity: 0.6 }}>
          {t("ml.createStepDescription")}
        </Typography>
        <Box
          component="div"
          sx={{ display: "flex", flexDirection: "column", gap: 3, mt: 4 }}
        >
          <TextField
            required
            fullWidth
            id="name"
            label={t("ml.createStepNameField")}
            value={name}
            onChange={onNameChange}
            error={!!nameError}
            helperText={nameError}
          />
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
                label={t("ml.createStepLinkField")}
                required
                error={!!folderNameError}
                helperText={folderNameError}
              />
            )}
          />
          <FormControl required fullWidth sx={{ mt: 1 }}>
            <InputLabel id="create-step-type-select-label">
              {t("ml.createStepTypeField")}
            </InputLabel>
            <Select
              labelId="create-step-type-select-label"
              value={type}
              label={t("ml.createStepTypeField")}
              onChange={onTypeChange}
              error={!!typeError}
            >
              {Object.values(ProjectType).map((type) => (
                <MenuItem key={type} value={type}>
                  {t(`types.${type}`)}
                </MenuItem>
              ))}
              {Object.values(AdditionalMLDataType).map((type) => (
                <MenuItem key={type} value={type}>
                  {t(`types.${type}`)}
                </MenuItem>
              ))}
            </Select>
            {!!typeError && (
              <FormHelperText error={true}>{typeError}</FormHelperText>
            )}
          </FormControl>
          {!!error && <Alert severity="error">{error}</Alert>}
        </Box>
      </Box>
      <Box component="div" sx={{ display: "flex", gap: 1.5, minWidth: 500 }}>
        <Button variant="outlined" fullWidth onClick={onCancel}>
          {t("general.cancel")}
        </Button>
        <Button
          variant="contained"
          fullWidth
          onClick={onCreate}
          disabled={!!nameError || !!folderNameError || !!typeError}
        >
          {t("ml.createButton")}
        </Button>
      </Box>
    </Box>
  );
};
