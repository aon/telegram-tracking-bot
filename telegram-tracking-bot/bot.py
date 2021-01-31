# Module imports
import telegram
from telegram.ext import Updater
from telegram.ext import CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler, Filters, TypeHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import logging as log

class Bot:
    def __init__(self, sched, database, providers, token):
        self.bot = telegram.Bot(token=token)
        self.updater = Updater(token=token, use_context=True)    
        self.dispatcher = self.updater.dispatcher
        self.sched = sched
        self.prov = providers
        self.db = database
        self._handlers()
        log.info("Bot started")

    def _handlers(self):
        self._start_handler()
        self._add_handler()
        self._admin_handler()
        self._contact_handler()
        
    # ---------- Handler functions ----------- #
    def _start_handler(self):
        """
        /start handler

        Should give basic info about how the bot works
        and what options there are.
        """
        # --------- Local functions ---------- #
        def main(update, context):
            ANSWER_TEXT = (
                "Hola! Soy un bot que trackea envíos.\n"
                "\n"
                "Elegí una opción:"
            )
            # Checks if it comes from a submenu (query) or not
            if update.callback_query:
                query = update.callback_query
                query.answer()
                query.edit_message_text(
                    text=ANSWER_TEXT,
                    reply_markup=main_menu_keyboard()
                )
            else:
                update.message.reply_text(
                    text=ANSWER_TEXT,
                    reply_markup=main_menu_keyboard()
                )

        # --------- Keyboards ----------- #
        def main_menu_keyboard():
            """
            Used in start and return handler
            """
            names = ["Agregar", "Administrar", "Contacto"]
            callbacks = ["add", "admin", "contact"]
            keyboard = self._make_keyboard(names, callbacks, 1)
            return(keyboard)

        # -------------- Handlers ------------ #
        self.dispatcher.add_handler(CommandHandler('start', main))
        self.dispatcher.add_handler(CommandHandler('help', main))
        self.dispatcher.add_handler(CommandHandler('ayuda', main))
        self.dispatcher.add_handler(CallbackQueryHandler(main, pattern='main'))
    
    def _add_handler(self):
        """
        Adds new tracking number through menu
        """

        # ------ States ----- #
        TRACKNUM = 1
        NAME = 2
        FINAL = 3

        # ------ Local functions ------ #
        def get_company(update, context):
            query = update.callback_query
            query.answer()
            query.edit_message_text(
                text="Bien! Elegí por qué compañía viene el envío. \n\n Si querés cancelar, mandame /cancel",
                reply_markup=get_company_keyboard()
            )
            
            return TRACKNUM
        
        def get_tracknum(update, context):
            query = update.callback_query
            query.answer()
            
            # Get company value
            context.user_data["company"] = query.data
            
            # Answer message
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Perfecto, decime ahora el número de tracking. \n\n Si querés cancelar, mandame /cancel"
                )
            return NAME

        def get_name(update, context):
            tracknum = update.message.text

            # Check if tracknum not null
            if not tracknum:
                context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="Parece que no mandaste nada! Decime el número de tracking. \n\n Si querés cancelar, mandame /cancel"
                )
                return TRACKNUM
            # TODO check it's a real number
            
            # Check if tracknum already added
            exists = self.db.check_tracknum_exists(update.effective_chat.id, tracknum, context.user_data["company"])
            if exists:
                context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text="El número de tracking ya existe con el nombre: {} Agregá otro! \n\n Si querés cancelar, mandame /cancel".format(exists)
                    )
                return TRACKNUM
            
            # Everything cool, proceed
            context.user_data["tracknum"] = tracknum

            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Último paso! Decime con qué nombre querés identificar este tracking. \n\n Si querés cancelar, mandame /cancel"
            )
            return FINAL

        def final(update, context):

            # Check if name not null
            if not update.message.text:
                context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="Parece que no mandaste nada! Decime un nombre para identificar el tracking. \n\n Si querés cancelar, mandame /cancel"
                )
                return NAME

            # Check if name already exists
            exists = self.db.check_name_exists(update.effective_chat.id, update.message.text)
            if exists:
                context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text="El nombre ya existe para el tracking: {} \nDecime otro! \n\n Si querés cancelar, mandame /cancel".format(exists)
                    )
                return NAME
            
            # Everything cool, proceed
            context.user_data["name"] = update.message.text

            # Response
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Número de tracking agregado!"
            )

            # Add it
            self.db.add_tracknum(
                update.effective_chat.id,
                context.user_data["tracknum"],
                context.user_data["company"],
                context.user_data["name"]
                )

            self.sched.add_tracknum_job(
                update.effective_chat.id,
                context.user_data["tracknum"],
                context.user_data["company"]
                )

            return ConversationHandler.END

        def cancel(update, context):
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Bueno, dale /start si querés volver al menú principal!"
            )
            return ConversationHandler.END

        def nothing(update, context):
            return ConversationHandler.END

        # --------- Keyboards ----------- #
        def get_company_keyboard():
            
            keyboard = self._make_keyboard(self.prov.real_names, self.prov.supported, 2, volver=True)
            return(keyboard)
        
        # --------- Handlers ---------- #
        self.dispatcher.add_handler(ConversationHandler(
            entry_points=[CallbackQueryHandler(get_company, pattern="add"), CommandHandler("add", get_company)],
            states={
                TRACKNUM: [CallbackQueryHandler(get_tracknum, pattern="|".join(self.prov.supported))],
                NAME: [MessageHandler(Filters.text & (~Filters.command), get_name)],
                FINAL: [MessageHandler(Filters.text & (~Filters.command), final)]
                },
            fallbacks=[CommandHandler("cancel",cancel), TypeHandler(telegram.Update, nothing)],
            allow_reentry=True
        ), group=3)

    def _admin_handler(self):
        """
        Used to admin trackings
        """
        # ------ States ----- #
        TRACKNUM_OPTIONS = 1
        OPTION_HANDLER = 2
        
        # ----------- Local funtions ----------- #
        def admin(update, context):
            query = update.callback_query
            query.answer()
            tracknum_names = self.db.get_user_tracknums(update.effective_chat.id)
            
            if not tracknum_names:
                keyboard = self._make_keyboard(["Volver"],["main"],1)
                query.edit_message_text(
                    text="Acá vas a poder administrar tus trackings... cuando agregues uno.\n",
                    reply_markup=keyboard
                )
                return ConversationHandler.END
            else:
                names = [x[1] for x in tracknum_names]
                keyboard = self._make_keyboard(names, names, 2, volver=True)
                query.edit_message_text(
                    text="Seleccioná un tracking de la lista:\n",
                    reply_markup=keyboard
                )
                return TRACKNUM_OPTIONS

        def tracknum_options(update, context):
            query = update.callback_query
            query.answer()

            # Check if volver pressed
            if query.data == "main":
                return ConversationHandler.END
            
            # Get tracking information from selected trackname
            context.user_data["name"] = query.data
            track_and_comp = self.db.get_tracknum_and_company_by_name(update.effective_chat.id, query.data)
            context.user_data["tracknum"], context.user_data["company"] = track_and_comp

            # Show options
            options = ["Borrar", "Ver última info"]
            keyboard = self._make_keyboard(options, ["delete", "info"], 2, volver=True, volver_callback="admin")
            query.edit_message_text(
                    text="Seleccioná una opción:\n",
                    reply_markup=keyboard
                )
            return OPTION_HANDLER

        def option_handler(update, context):
            query = update.callback_query
            query.answer()

            tracknum = context.user_data["tracknum"]
            company = context.user_data["company"]

            if query.data == "delete":

                # This gets done only if nobody else has it
                if not self.db.check_anyone_else_has_tracknum(tracknum, company):
                    self.sched.del_tracknum_job(tracknum, company)
                    self.db.del_tracknum_info(tracknum, company)

                # This is always
                self.db.del_tracknum_user(update.effective_chat.id, tracknum, company)
                context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="Tracking borrado exitosamente! Dale /start para volver al menú principal."
                )

            if query.data == "info":
                info = self.db.get_existing_info(tracknum, company)
                self.send_update([update.effective_chat.id], tracknum, company, info, False)
                context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="Dale /start para volver al menú principal."
                )
            return ConversationHandler.END

        def cancel(update, context):
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Bueno, dale /start si querés volver al menú principal!"
            )
            return ConversationHandler.END

        def nothing(update, context):
            return ConversationHandler.END

        # ----------- Handlers ------------ #
        self.dispatcher.add_handler(ConversationHandler(
            entry_points=[CallbackQueryHandler(admin, pattern="admin"), CommandHandler("admin", admin)],
            states={
                TRACKNUM_OPTIONS: [CallbackQueryHandler(tracknum_options)],
                OPTION_HANDLER: [CallbackQueryHandler(option_handler)]
                },
            fallbacks=[CommandHandler("cancel",cancel), TypeHandler(telegram.Update, nothing)],
            allow_reentry=True
        ), group=3)

    def _contact_handler(self):
        """
        Used to contact the github repo
        """
        # --------- Local functions ---------- #
        def main(update, context):
            query = update.callback_query
            query.answer()
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Si tenés alguna duda, sugerencia o querés colaborar, te podés contactar abriendo un issue en el repositorio del proyecto: https://github.com/aon/telegram-tracking-bot"
            )
        self.dispatcher.add_handler(CallbackQueryHandler(main, pattern="contact"))

    # ----------- External methods ----------- #
    def send_update(self, chat_ids: list, tracknum: str,
        company: str, info: list, new: bool):
        """
        Sends new information update to all
        chat_ids registered to follow that tracking number.
        """
        list_text = ""

        # Turns it into string
        for row in info:
            list_text += "{}\n{}\n{}\n\n".format(
                row["date"],
                row["description"],
                row["location"]
            )
            
        # Sends update to all chat ids
        if new:
            ANSWER_TEXT = "Tenés nueva información de tu envío: "
        else:
            ANSWER_TEXT = "Información existente de tu envío: "
        for chat_id in chat_ids:
            name = self.db.get_tracknum_name(tracknum, chat_id, company)
            self.bot.send_message(
                chat_id=chat_id,
                text=ANSWER_TEXT + "{} ({})\n".format(name, tracknum)
                     + "\n"
                     + list_text
            )

    # ------------ Static methods ------------ #
    @staticmethod
    def _make_keyboard(
        names: list, callbacks: list, columns: int,
        volver: bool = False, volver_callback: str = "main") -> InlineKeyboardMarkup:
        """
        Gets a list of button names, callbacks and number of columns
        and turns it into a keyboard markup.

        Param:
            - names: list of button names
            - callbacks: list of callbacks for each button
            - columns: number of columns to use
            - volver: adds a "volver" button, default = True
            - volver_callback: callback for "volver" button, default = "main"
        """
        if len(names) != len(callbacks):
            raise Exception("Callback list and name list should be same length")
            
        keyboards = []
        for i, name in enumerate(names):
            keyboards.append(
                InlineKeyboardButton(name, callback_data=callbacks[i])
            )
        
        if columns == 1:
            return_keyboard = [[x] for x in keyboards]
        else:
            return_keyboard = []
            for i, item in enumerate(keyboards):
                if i%columns == 0:
                    return_keyboard.append([item])
                else:
                    return_keyboard[int(i/columns)].append(item)
        
        # If the last list is missing one column, adds the Volver button there
        # otherwise it will use a full row
        if volver:
            volver_button = InlineKeyboardButton("Volver", callback_data=volver_callback)
            if len(return_keyboard[-1]) < columns:
                return_keyboard[-1].append(volver_button)
            else:
                return_keyboard.append([volver_button])

        return InlineKeyboardMarkup(return_keyboard)

if __name__ == "__main__":
    pass