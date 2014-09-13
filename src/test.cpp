#include <stdlib.h>
#include <gtk/gtk.h>
#include <gtkscintilla.h>
#include <cstdio>

static void helloWorld (GtkWidget *wid, GtkWidget *win)
{
  printf("HELLO W\n");
}

static void onKey (GtkWidget *wid, gint key, gint modifier, GtkWidget *win)
{
  printf("KEY %d %d\n", key, modifier);
}

int main (int argc, char *argv[])
{
  GtkWidget *button = NULL;
  GtkWidget *win = NULL;
  GtkWidget *vbox = NULL;
  GtkWidget *sci = NULL;

  /* Initialize GTK+ */
  g_log_set_handler ("Gtk", G_LOG_LEVEL_WARNING, (GLogFunc) gtk_false, NULL);
  gtk_init (&argc, &argv);
  g_log_set_handler ("Gtk", G_LOG_LEVEL_WARNING, g_log_default_handler, NULL);

  /* Create the main window */
  win = gtk_window_new (GTK_WINDOW_TOPLEVEL);
  gtk_container_set_border_width (GTK_CONTAINER (win), 8);
  gtk_window_set_title (GTK_WINDOW (win), "Hello World");
  gtk_window_set_position (GTK_WINDOW (win), GTK_WIN_POS_CENTER);
  gtk_widget_realize (win);
  g_signal_connect (win, "destroy", gtk_main_quit, NULL);

  /* Create a vertical box with buttons */
  vbox = gtk_vbox_new (TRUE, 6);
  gtk_container_add (GTK_CONTAINER (win), vbox);

  button = gtk_button_new_from_stock (GTK_STOCK_DIALOG_INFO);
  g_signal_connect (G_OBJECT (button), "clicked", G_CALLBACK (helloWorld), (gpointer) win);

  gtk_box_pack_start (GTK_BOX (vbox), button, TRUE, TRUE, 0);

  sci = gtk_scintilla_new();
  gtk_box_pack_start (GTK_BOX (vbox), sci, TRUE, TRUE, 0);
    g_signal_connect (G_OBJECT (sci), "key", G_CALLBACK (onKey), NULL);

  /* Enter the main loop */
  gtk_widget_show_all (win);
  gtk_main ();
  return 0;
}

