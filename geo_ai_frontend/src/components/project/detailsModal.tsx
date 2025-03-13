import React from "react";
import { useTranslation } from "react-i18next";
import {
  Box,
  Button,
  IconButton,
  Link,
  Modal,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableRow,
  Typography,
} from "@mui/material";
import CloseIcon from "@mui/icons-material/Close";

import { ModalContent } from "@components/shared/modalContent";
import { ModalProps } from "@models/common";
import { Project, ProjectStatus } from "@models/project";
import { StatusLabel } from "@components/shared/statusLabel";
import { ERRORS } from "@models/error";

const nextcloudURL = import.meta.env.VITE_NEXTCLOUD_URL;

interface DetailsModalProps extends ModalProps {
  project: Project;
}

export const ProjectDetailsModal: React.FC<DetailsModalProps> = ({
  project,
  isOpen,
  onClose,
}) => {
  const { t } = useTranslation();

  const handleClose = () => {
    onClose();
  };

  return (
    <Modal open={isOpen} onClose={handleClose}>
      <ModalContent>
        <IconButton
          sx={{ alignSelf: "end" }}
          onClick={handleClose}
          id="close-modal-button"
        >
          <CloseIcon />
        </IconButton>
        <Typography
          variant="h5"
          textAlign="center"
          sx={{ overflowWrap: "anywhere" }}
        >
          {t("project.details")}
        </Typography>
        <TableContainer>
          <Table sx={{ mt: 4 }}>
            <TableBody>
              <TableRow>
                <TableCell>{t("project.name")}</TableCell>
                <TableCell sx={{ overflowWrap: "anywhere" }}>
                  {project.name}
                </TableCell>
              </TableRow>
              <TableRow>
                <TableCell>{t("general.dateCreated")}</TableCell>
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
              </TableRow>
              <TableRow>
                <TableCell>{t("general.createdBy")}</TableCell>
                <TableCell sx={{ overflowWrap: "anywhere" }}>
                  {project.created_by}
                </TableCell>
              </TableRow>
              <TableRow>
                <TableCell>{t("project.type")}</TableCell>
                <TableCell>{t(`types.${project.type}`)}</TableCell>
              </TableRow>
              <TableRow>
                <TableCell>{t("project.status")}</TableCell>
                <TableCell>
                  <StatusLabel status={project.status} />
                </TableCell>
              </TableRow>
              {project.super_resolution && (
                <TableRow>
                  <TableCell>{t("project.qualitySettingTitle")}</TableCell>
                  <TableCell>{project.super_resolution}</TableCell>
                </TableRow>
              )}
              {project.status === ProjectStatus.Error && (
                <TableRow>
                  <TableCell>{t("general.errorTitle")}</TableCell>
                  <TableCell sx={{ overflowWrap: "anywhere" }}>
                    {(project.error_code && ERRORS[project.error_code]
                      ? t(ERRORS[project.error_code])
                      : project.description) || t(ERRORS.OTHER)}
                  </TableCell>
                </TableRow>
              )}
              <TableRow>
                <TableCell>{t("project.dateShooted")}</TableCell>
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
              </TableRow>
              <TableRow>
                <TableCell>{t("project.folderName")}</TableCell>
                <TableCell>
                  <Link
                    href={`${nextcloudURL}/?dir=/${project.link}`}
                    target="_blank"
                    underline="hover"
                    id="nextcloud-link"
                  >
                    {project.link}
                  </Link>
                </TableCell>
              </TableRow>
              {!!project.ml_model?.length && (
                <TableRow>
                  <TableCell>{t("project.mlSettingTitle1")}</TableCell>
                  <TableCell sx={{ overflowWrap: "anywhere" }}>
                    {project.ml_model.join(", ")}
                  </TableCell>
                </TableRow>
              )}
              {!!project.ml_model_deeplab?.length && (
                <TableRow>
                  <TableCell>{t("project.mlSettingTitle2")}</TableCell>
                  <TableCell sx={{ overflowWrap: "anywhere" }}>
                    {project.ml_model_deeplab.join(", ")}
                  </TableCell>
                </TableRow>
              )}
              {!!project.classes?.length && (
                <TableRow>
                  <TableCell>{t("ml.listOfClasses")}</TableCell>
                  <TableCell sx={{ overflowWrap: "anywhere" }}>
                    {project.classes.join(", ")}
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </TableContainer>
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
            variant="text"
            onClick={handleClose}
            fullWidth
            id="close-modal-button"
          >
            {t("general.close")}
          </Button>
        </Box>
      </ModalContent>
    </Modal>
  );
};
